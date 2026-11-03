"""SAM 3.1 image segmentation through Meta Responses; one paid-call boundary."""
import base64
import hashlib
import io
import json
import os
import urllib.request
from pathlib import Path

from PIL import Image

from . import llm

MODEL = "sam-3.1"
IMAGE_USD = 2.50 / 1000  # https://dev.meta.ai/models/sam-3-1


def segment(png_bytes, prompts):
    """One concept per request, cached and charged to the existing Muse ledger/caps.

    Returns the original Responses JSON for each concept; HTTP failures propagate
    with their status and response body, without retries or a substitute model.
    """
    if not isinstance(prompts, (list, tuple)) or not 1 <= len(prompts) <= 8 or any(
            not isinstance(p, str) or not p.strip() or len(p) > 100 for p in prompts):
        raise ValueError("give 1–8 short concept prompts")
    with Image.open(io.BytesIO(png_bytes)) as image:
        if image.format != "PNG" or image.width * image.height > 25_000_000:
            raise ValueError("give a PNG of at most 25 megapixels")
        image.verify()
    outputs = []
    for prompt in prompts:
        key = hashlib.sha256(MODEL.encode() + prompt.encode() + png_bytes).hexdigest()
        hit = llm.CACHE / f"sam-{key}.json"
        if hit.exists():  # cache files are atomic; a replay need not queue behind unrelated paid calls
            outputs.append(json.loads(hit.read_text()))
            continue
        with llm._billing_lock():
            if hit.exists():
                outputs.append(json.loads(hit.read_text()))
                continue
            cap = getattr(llm._SPEND_CAP, "value", None)
            if cap and llm.spent_here() - cap[0] + IMAGE_USD > cap[1]:
                raise llm.BudgetExceeded("task budget would be exceeded by SAM; no call made")
            if llm._provider_spend(MODEL) + IMAGE_USD > llm._budget(MODEL):
                raise llm.BudgetExceeded("Muse budget would be exceeded by SAM; no call made")
            llm._load_env()
            body = {"model": MODEL, "input": [{"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": "data:image/png;base64," + base64.b64encode(png_bytes).decode()},
            ]}], "stream": False, "metadata": {"mask_encoding": "one_bit", "include_confidence": "true"}}
            request = urllib.request.Request(os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/") + "/responses",
                                             data=json.dumps(body).encode(), method="POST", headers={
                                                 "Authorization": "Bearer " + os.environ["META_API_KEY"],
                                                 "Content-Type": "application/json", "Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=180) as response:
                raw = response.read()
            # A successful HTTP request is billable even if its body cannot be parsed.
            llm._append_usage({"model": MODEL, "provider": "meta", "tag": llm.current_tag() or "meta",
                               "in": 0, "out": 0, "images": 1, "usd": IMAGE_USD})
            result = {"prompt": prompt, "response": json.loads(raw)}
            llm.CACHE.mkdir(parents=True, exist_ok=True)
            temp = hit.with_suffix(".tmp")
            temp.write_text(json.dumps(result))
            os.replace(temp, hit)
            outputs.append(result)
    return {"model": MODEL, "image_sha256": hashlib.sha256(png_bytes).hexdigest(), "outputs": outputs}


def assistance(png_bytes, segmentation, folder):
    """Decode real masks with Meta's parser; save numbered regions and context crops."""
    from meta_sam_parser import CompletedOutcome, SegmentationMaskRecord, decode_mask_to_raster, image_segmentation_format
    from PIL import ImageDraw, ImageFont

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(png_bytes)) as source:
        image = source.convert("RGB")
    overlay = image.convert("RGBA")
    rows, crops = [], []
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    for output in segmentation["outputs"]:
        response = output["response"]
        if response.get("status") != "completed" or response.get("error"):
            raise ValueError("SAM response did not complete: " + json.dumps(response.get("error")))
        text = "".join(part.get("text", "") for message in response.get("output", [])
                       for part in message.get("content", []) if part.get("type") == "output_text")
        parser = image_segmentation_format().create_parser()
        parser.push(text)
        parsed = parser.finish(CompletedOutcome()).result
        errors = [d.message for d in parsed.diagnostics if d.severity == "error"]
        if errors:
            raise ValueError("Malformed SAM output: " + "; ".join(errors))
        for record in parsed.records:
            if not isinstance(record, SegmentationMaskRecord):
                continue
            box = [int(record.bounds.left), int(record.bounds.top), int(record.bounds.right), int(record.bounds.bottom)]
            x0, y0, x1, y1 = box
            if not 0 <= x0 < x1 <= image.width or not 0 <= y0 < y1 <= image.height:
                raise ValueError("SAM box lies outside the source image")
            if (record.mask.width, record.mask.height) != (x1 - x0, y1 - y0):
                raise ValueError("SAM mask size does not match its box")
            number = f"R{len(rows) + 1:03d}"
            mask = Image.frombytes("L", (record.mask.width, record.mask.height), decode_mask_to_raster(record.mask)).point(lambda p: p * 255)
            mask.save(folder / f"{number}-mask.png")
            colour = (230, 70, 35) if output["prompt"] == "pipe" else (20, 120, 210)
            tint = Image.new("RGBA", mask.size, (*colour, 0))
            tint.putalpha(mask.point(lambda p: p * 90 // 255))
            overlay.alpha_composite(tint, (x0, y0))
            draw = ImageDraw.Draw(overlay)
            draw.rectangle(box, outline=(*colour, 255), width=3)
            draw.text((x0, max(0, y0 - 26)), number, fill=(*colour, 255), font=font)
            padded = [max(0, x0 - 35), max(0, y0 - 35), min(image.width, x1 + 35), min(image.height, y1 + 35)]
            crop = image.crop(padded)
            crop.save(folder / f"{number}-crop.png")
            crops.append((number, output["prompt"], crop))
            rows.append({"id": number, "concept": output["prompt"], "object_id": record.object_id,
                         "box_px": box, "box_fraction": [round(x0 / image.width, 5), round(y0 / image.height, 5),
                                                           round(x1 / image.width, 5), round(y1 / image.height, 5)],
                         "crop_box_px": padded, "confidence": record.confidence})
    overlay.save(folder / "overlay.png")
    preview = overlay.convert("RGB")
    preview.thumbnail((900, 900))
    preview.save(folder / "overlay.jpg", quality=55)
    # At most 24 context crops go into the contact sheet; every mask/crop/coordinate remains on disk.
    sheet = Image.new("RGB", (720, max(160, ((min(24, len(crops)) + 3) // 4) * 160)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (number, concept, crop) in enumerate(crops[:24]):
        crop.thumbnail((170, 125))
        x, y = (index % 4) * 180, (index // 4) * 160
        sheet.paste(crop, (x, y + 32))
        draw.text((x + 3, y + 3), number + " " + concept, fill="black")
    sheet.save(folder / "crops.jpg", quality=55)
    manifest = {"source_size_px": [image.width, image.height], "overlay_size_px": list(preview.size), "regions": rows,
                "crop_sheet_regions": [r[0] for r in crops[:24]], "overlay": "overlay.jpg", "crops": "crops.jpg"}
    (folder / "regions.json").write_text(json.dumps(manifest, indent=2))
    return manifest

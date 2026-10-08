import json
import os
import re
import time

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths
from nodes import LoadImage


# Not a subclass of LoadImage, inheriting its ESSENTIALS_CATEGORY makes the frontend list this node as a core node.
class LoadImageWithFilename:
    INPUT_TYPES = LoadImage.INPUT_TYPES
    IS_CHANGED = LoadImage.IS_CHANGED
    VALIDATE_INPUTS = LoadImage.VALIDATE_INPUTS

    CATEGORY = "QoL/image"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "filename")
    FUNCTION = "load_image_with_filename"

    def load_image_with_filename(self, image):
        output_image, output_mask = LoadImage().load_image(image)
        image_path = folder_paths.get_annotated_filepath(image)
        filename = os.path.splitext(os.path.basename(image_path))[0]
        return (output_image, output_mask, filename)


def parse_time_tokens(text):
    text = text.replace("[time]", str(int(time.time())))
    return re.sub(r"\[time\((.*?)\)\]", lambda m: time.strftime(m.group(1)), text)


# Based on "Image Save" from WAS Node Suite (MIT). A number padding of 0 saves without a counter.
class ImageSave:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "output_path": ("STRING", {"default": "[time(%Y-%m-%d)]"}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "filename_delimiter": ("STRING", {"default": "_"}),
                "filename_number_padding": ("INT", {"default": 0, "min": 0, "max": 9, "step": 1, "tooltip": "0 saves without a number, existing files with the same name are overwritten."}),
                "filename_number_start": ("BOOLEAN", {"default": False}),
                "extension": (["png", "jpg", "jpeg", "gif", "tiff", "webp", "bmp"],),
                "dpi": ("INT", {"default": 300, "min": 1, "max": 2400, "step": 1}),
                "quality": ("INT", {"default": 100, "min": 1, "max": 100, "step": 1}),
                "optimize_image": ("BOOLEAN", {"default": True}),
                "lossless_webp": ("BOOLEAN", {"default": False}),
                "embed_workflow": ("BOOLEAN", {"default": True}),
                "show_previews": ("BOOLEAN", {"default": True}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "files")
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "QoL/image"

    def save_images(self, images, output_path, filename_prefix, filename_delimiter, filename_number_padding, filename_number_start,
                    extension, dpi, quality, optimize_image, lossless_webp, embed_workflow, show_previews, prompt=None, extra_pnginfo=None):
        output_dir = folder_paths.get_output_directory()
        filename_prefix = parse_time_tokens(filename_prefix)
        output_path = os.path.join(output_dir, parse_time_tokens(output_path))
        os.makedirs(output_path, exist_ok=True)

        delimiter = filename_delimiter
        padding = filename_number_padding
        counter = 1
        if padding > 0:
            if filename_number_start:
                pattern = f"(\\d+){re.escape(delimiter)}{re.escape(filename_prefix)}"
            else:
                pattern = f"{re.escape(filename_prefix)}{re.escape(delimiter)}(\\d+)"
            existing_counters = [int(m.group(1)) for m in (re.match(pattern, f) for f in os.listdir(output_path)) if m]
            if existing_counters:
                counter = max(existing_counters) + 1

        results = []
        output_files = []
        for image in images:
            img = Image.fromarray(np.clip(255. * image.cpu().numpy(), 0, 255).astype(np.uint8))

            if extension == "webp":
                img_exif = img.getexif()
                if embed_workflow:
                    if prompt is not None:
                        img_exif[0x010f] = "Prompt:" + json.dumps(prompt)
                    if extra_pnginfo is not None:
                        img_exif[0x010e] = "Workflow:" + "".join(json.dumps(extra_pnginfo[x]) for x in extra_pnginfo)
                exif_data = img_exif.tobytes()
            else:
                exif_data = PngInfo()
                if embed_workflow:
                    if prompt is not None:
                        exif_data.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            exif_data.add_text(x, json.dumps(extra_pnginfo[x]))

            if padding == 0:
                file = f"{filename_prefix}.{extension}"
            elif filename_number_start:
                file = f"{counter:0{padding}}{delimiter}{filename_prefix}.{extension}"
            else:
                file = f"{filename_prefix}{delimiter}{counter:0{padding}}.{extension}"
            counter += 1

            output_file = os.path.abspath(os.path.join(output_path, file))
            if extension in ["jpg", "jpeg"]:
                img.save(output_file, quality=quality, optimize=optimize_image, dpi=(dpi, dpi))
            elif extension == "webp":
                img.save(output_file, quality=quality, lossless=lossless_webp, exif=exif_data)
            elif extension == "png":
                img.save(output_file, pnginfo=exif_data, optimize=optimize_image, dpi=(dpi, dpi))
            elif extension == "bmp":
                img.save(output_file)
            elif extension == "tiff":
                img.save(output_file, quality=quality, optimize=optimize_image)
            else:
                img.save(output_file, pnginfo=exif_data, optimize=optimize_image)
            output_files.append(output_file)

            subfolder = os.path.relpath(os.path.dirname(output_file), output_dir)
            results.append({"filename": file, "subfolder": "" if subfolder == "." else subfolder, "type": "output"})

        return {"ui": {"images": results if show_previews else []}, "result": (images, output_files)}


NODE_CLASS_MAPPINGS = {
    "QoLLoadImageWithFilename": LoadImageWithFilename,
    "QoLImageSave": ImageSave,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QoLLoadImageWithFilename": "Load Image (with Filename)",
    "QoLImageSave": "Image Save (QoL)",
}

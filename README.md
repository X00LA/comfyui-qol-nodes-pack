# ComfyUI QoL Nodes Pack

Small quality-of-life nodes for ComfyUI. All nodes are in the `QoL/image` category.

## Nodes

**Load Image (with Filename)**
Same as the core "Load Image" node, with an extra `filename` output: the image's file name without its extension (`photo.png` → `photo`).

**Image Save (QoL)**
Based on "Image Save" from [WAS Node Suite](https://github.com/WASasquatch/was-node-suite-comfyui).
- `filename_number_padding` = 0 saves as `<prefix>.<extension>` with no counter. Existing files with the same name are overwritten, and in a batch only the last image is kept.
- `filename_number_padding` = 1–9 appends a counter like WAS does (`ComfyUI_0001.png`).
- `output_path` and `filename_prefix` support `[time]` and `[time(<strftime format>)]`, e.g. `[time(%Y-%m-%d)]`.

Connect `filename` from "Load Image (with Filename)" to `filename_prefix` to save a processed image under its original name.

## Installation

```
cd ComfyUI/custom_nodes
git clone <repo-url> comfyui-qol-nodes-pack
```

Restart ComfyUI. No extra dependencies.

## License

MIT, see [LICENSE](LICENSE).

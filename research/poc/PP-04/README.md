# PP-04 Open XML SDK / PresentationML PoC

This is a candidate-backend experiment for `ADP-PP-04-01` and `VERIFY-ADP-PP-04-01`. It is not a YoloongPPT product runtime and does not select .NET or Open XML SDK as the product architecture.

## Fixed inputs and versions

- Candidate packages: `DocumentFormat.OpenXml` 3.5.1, `DocumentFormat.OpenXml.Framework` 3.5.1, and transitive `System.IO.Packaging` 10.0.2; all are MIT licensed. Exact resolutions are pinned in `packages.lock.json`.
- PoC container: `mcr.microsoft.com/dotnet/sdk:10.0` resolved to repository digest `sha256:e70cdb7f80b0348f5cb85f19a8f670fca061f033d57eed12fa003d58b0e06317`; observed SDK version `10.0.401`. These are PoC environment observations only.
- Real source package: `scanny/python-pptx` commit `278b47b1dedd5b46ee84c286e77cdfb0bf4594be`, `src/pptx/templates/default.pptx`, MIT license (text retained in `fixtures/LICENSE.python-pptx.txt`), SHA-256 `e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34`.

## Run in Docker

From the repository root, run the pinned SDK image with the project tree mounted:

```powershell
docker run --rm --mount type=bind,source=F:/YoloongPPT,target=/workspace --workdir /workspace/research/poc/PP-04 --env YPP_POC_IMAGE=mcr.microsoft.com/dotnet/sdk@sha256:e70cdb7f80b0348f5cb85f19a8f670fca061f033d57eed12fa003d58b0e06317 --env YPP_DOTNET_SDK_VERSION=10.0.401 mcr.microsoft.com/dotnet/sdk@sha256:e70cdb7f80b0348f5cb85f19a8f670fca061f033d57eed12fa003d58b0e06317 sh -lc 'test "$(dotnet --version)" = "$YPP_DOTNET_SDK_VERSION" && dotnet restore --locked-mode && dotnet run --no-restore'
```

The run opens the fixed template, records package inventory, adds one slide with title/body placeholders linked to a source layout, validates the output with `OpenXmlValidator`, compares master/layout/theme parts, injects an unknown package part for a preservation check, and records a truncated-package failure case. A second case adds a rectangle with fixed fill/stroke and explicit EMU geometry, saves the deck, reopens it, updates that shape's text, then checks its ID/name/geometry/fill/stroke and validates the saved file. A third case embeds a deterministic 1x1 PNG, saves and reopens the deck, replaces the bytes behind the existing image relationship, and verifies the before/after image SHA-256, relationship, content type, alt text, identity, EMU bounds, and validator result. Generated evidence is stored under `artifacts/`.

The recorded run produced one slide, retained the counts for one master, 11 layouts, and one theme, and reported zero Office 2019 validator errors for the new-slide output, shape-mutation output, and image-round-trip output. The probe text changed from `Existing shape before edit` to `Existing shape after edit`; shape ID/name, `rect` geometry, fill `4472C4`, outline `1F1F1F`, and EMU values `914400,457200,3657600,1828800` remained stable. The image probe replacement changed the stored PNG hash while retaining the image relationship, content type, alt text, shape ID/name, and EMU bounds (`914400,457200,1828800,914400`). The injected unknown package part remained byte-identical. Two slide-layout XML hashes changed during SDK serialization, while the selected master/layout/theme XML parts compared equal after normalizing namespace declarations, attribute order, and insignificant formatting whitespace. These are structural and byte-level checks, not a PowerPoint rendering check. The output was not rendered in PowerPoint or LibreOffice.

## Current scope limits

The shape-mutation case reopens a deck and edits a shape created earlier by this same PoC; it does not test editing a pre-populated third-party slide. Image coverage is limited to one embedded 1x1 PNG add/replace/read round trip. Crop, contain/cover, rotation, transparency, compression, linked images, image rendering, and broad third-party image compatibility remain untested. Table/chart/notes/comments/transition/animation/media authoring, other AutoShape types/adjustments/rotation, Office/LibreOffice rendering, and broad third-party template compatibility remain separate checks. No product capability is marked Native from this PoC alone.

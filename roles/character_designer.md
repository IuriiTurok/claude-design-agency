# Character Designer

<!-- Paths: {AGENCY_ROOT} = this plugin's install dir -->

**Role:** Owns character, mascot, and 3D-prep asset engagements — pose sheets, multi-view generation, image-to-3D pipelines. These are asset-production projects, not brand-identity projects: the 4 mandatory brand deliverables do not apply, but quality gates do.

**Why this skill exists:** Three engagements (dobra-dia mascot, Emma 3D, green-mascot) ran ad-hoc with no owning skill. Result: 27–31MB sessions, 6+ manual correction rounds per session on hairstyle/scale/cut-off consistency — all catchable by a pre-review checklist.

## When to invoke

Any request involving: mascot or character design/redesign, pose sheets, multi-view generation (front/back/side/3/4), character upscaling, background removal batches, or image-to-3D model prep.

## Inputs

1. `<project>/style_directive.md` if the character belongs to a branded project — palette and proportion constraints are binding.
2. Client reference material (photos, existing mascot versions, logo to apply).
3. Prior version folders — read the latest version's inventory before generating anything new.

## Asset Contract (write BEFORE generating)

Create or update `<project>/character_style_guide.md` declaring:
- Character anatomy baseline: head-to-body ratio, hand size, distinguishing features (hairstyle, accessories) that must stay identical across every output.
- Output inventory: which poses, which views, canvas size, file format, background treatment (transparent via rembg unless stated otherwise).
- Palette tokens (from the style directive when one exists).

No image generation until the contract exists. This is the design-brief gate for character work.

## Pipeline

1. **Generate** via deterministic scripts in `{AGENCY_ROOT}/execution/` (extend the `generate_logo.py` pattern — prompt history and feedback logged per round, never freeform one-off calls).
2. **Consistency gate — BEFORE showing the user.** Run this checklist on every batch:
   - [ ] Identical anatomy baseline across all images (hairstyle, accessories, proportions).
   - [ ] Identical canvas size and character scale (±2% variance max).
   - [ ] No cut-off limbs, hair, or props at image edges.
   - [ ] Uniform background treatment (all rembg'd or none).
   - [ ] Multi-view sets (front/back/side/3/4) generated from the same base model, exported as separate files — never a combined sheet unless requested.
   Fix failures and regenerate before user review. The user is not the consistency checker.
3. **Upscale ONLY after poses are finalized.** Upscaling before final selection amplifies artifacts and wastes rounds.
4. **Iterate by file reference.** During feedback rounds, reference generated images by path (`assets/characters/<name>/pose_03.png`), never re-embed full image sets into the conversation — re-embedding bloats sessions and loses version history.
5. **Log feedback** each round to the generation script's feedback log (same discipline as `generate_logo.py --log-feedback`).

## Outputs

- `<project>/character_style_guide.md` — the asset contract (updated each engagement).
- `<project>/pose_sheet_inventory.md` — table of every generated asset: pose, view, file path, status (draft/approved/superseded).
- Assets under `<project>/assets/characters/<name>/`, versioned by folder (`v1/`, `v2/`) with the inventory marking the current version.

## What this skill does NOT do

- Brand strategy or style directives (Creative Director's domain).
- Logo design (Logo Designer's domain — even when the logo appears on the character; consume the approved logo file).
- Rigging or actual 3D modeling (prep only: clean multi-views + transparent PNGs ready for Meshy/Blender).

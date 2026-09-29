# Character Designer

<!-- Paths: {AGENCY_ROOT} = this plugin's install dir -->

**Role:** Owns character, mascot, and 3D asset engagements — pose sheets, multi-view generation, image-to-3D pipelines, and code-only procedural Three.js models from a reference image (img2threejs). These are asset-production projects, not brand-identity projects: the 4 mandatory brand deliverables do not apply, but quality gates do.

**Why this skill exists:** Three engagements (dobra-dia mascot, Emma 3D, green-mascot) ran ad-hoc with no owning skill. Result: 27–31MB sessions, 6+ manual correction rounds per session on hairstyle/scale/cut-off consistency — all catchable by a pre-review checklist.

## When to invoke

Any request involving: mascot or character design/redesign, pose sheets, multi-view generation (front/back/side/3/4), character upscaling, background removal batches, image-to-3D model prep, or code-only procedural Three.js models from a reference image (img2threejs).

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

## 3D track (img2threejs)

When the deliverable is a 3D model, invoke the external `img2threejs` skill at `~/.claude/skills/img2threejs` (Apache-2.0, installed as a user skill, not bundled with this plugin). It rebuilds the object or character in a reference image as a **code-only procedural Three.js model** — a TypeScript `THREE.Group` factory `create<Name>Model(spec, options)` — through a gated pipeline: intake/validation → pre-spec assessment + quality contract → detail inventory → sculpt spec → strict validation → locked build passes (blockout → structure → form → material → lighting → interaction → optimization) → per-pass render, comparison sheet, and deterministic gates → review decision (`continue | refine-spec | refine-code | request-input | stop`).

**Availability.** If `~/.claude/skills/img2threejs` is absent, print these commands for the user and stop. Never vendor, copy, or reimplement it:

```bash
git clone https://github.com/img2threejs/img2threejs ~/Code/vendor/img2threejs
ln -s ~/Code/vendor/img2threejs ~/.claude/skills/img2threejs
```

**Inputs.**
- The approved reference image: the front view from the pose-sheet pipeline above (marked `approved` in `pose_sheet_inventory.md`), or the client photo.
- Intended use: prop, hero render, or animation rig.
- Palette and proportion constraints from `style_directive.md` and `character_style_guide.md` (anatomy baseline, palette tokens). They go into the sculpt spec, not just the conversation.

**Profile.** `character` for mascots and characters; `generic` for props and objects. `animated-character` only when the rig must MOVE, and only via the optional `img2` harness (`npx github:img2threejs/img2 install`, then `img2 add img2threejs/plugin-character`). A `character` build has no animation-readiness gates, so never ship it as a moving rig.

**Working dir and outputs.** Everything lives in `<project>/3d/<name>/`, never in the skill directory:
- `.img2threejs/state.json` — the checklist authority
- `assessment.json` — pre-spec assessment + quality contract
- `object-sculpt-spec.json` — the sculpt spec
- `src/create<Name>Model.ts` — the generated factory
- `renders/` — per-pass renders and comparison sheets

Run the skill's scripts by path from that directory, so relative state and output paths land in the project:

```bash
# from <project>/3d/<name>/
I2T=~/.claude/skills/img2threejs
python3 $I2T/forge/state.py init --state .img2threejs/state.json --reference <approved-ref.png> --profile <character|generic> --spec object-sculpt-spec.json
python3 $I2T/forge/next.py --state .img2threejs/state.json object-sculpt-spec.json
```

**The state file is the checklist authority.** Always run `forge/next.py` first — at every start, resume, and before every correction iteration — and run the exact next command it prints (it prints `python3 forge/...`; prefix `forge/` with `$I2T/`). Exit code 3 or `status=stopped` is a hard stop: report the reason and request input. Never reconstruct progress from chat history, and never skip a step without `forge/state.py mark ... --reason`.

**Gates.**
1. **img2threejs gates first — the hard gate for likeness.** Its deterministic gates (turntable, self-intersection, attachment anchors, `diagnose_render`) and the per-pass comparison sheet (`forge/stage4_review/make_comparison_sheet.py --reference <img> --render <shot> --out renders/<pass>_cmp.png`) run on every pass. Fail a pass when an identity-defining feature from the anatomy baseline is wrong, even if the global score looks fine. Never claim "done" when a pass says "improved" — improved is not accepted.
2. **Then `visual-qa`** grades the rendered preview like any other deliverable.
3. **`style-enforcer`** checks the rendered palette against `style_directive.md`.

**Record each pass** in `pose_sheet_inventory.md`, or in a `<project>/3d_inventory.md` table:

| Pass | Fidelity score | Decision | Artifact path |
|------|----------------|----------|---------------|

**Honesty.** A single image cannot reveal hidden sides or guarantee exact geometry. State explicitly, in the inventory and to the client, where the model is approximate or stylized; supply the approved back/side views or accept stylization when hidden-side fidelity matters.

## Outputs

- `<project>/character_style_guide.md` — the asset contract (updated each engagement).
- `<project>/pose_sheet_inventory.md` — table of every generated asset: pose, view, file path, status (draft/approved/superseded).
- Assets under `<project>/assets/characters/<name>/`, versioned by folder (`v1/`, `v2/`) with the inventory marking the current version.
- 3D track: `<project>/3d/<name>/` containing `.img2threejs/state.json`, `assessment.json`, `object-sculpt-spec.json`, `src/create<Name>Model.ts`, and `renders/` (per-pass renders + comparison sheets); per-pass records in `pose_sheet_inventory.md` or `<project>/3d_inventory.md`.

## What this skill does NOT do

- Brand strategy or style directives (Creative Director's domain).
- Logo design (Logo Designer's domain — even when the logo appears on the character; consume the approved logo file).
- Photogrammetry, mesh downloads, or asset-pack sourcing (img2threejs is reconstruction-by-code); external GLB/VRM exports are optional plugin targets, not the build path.

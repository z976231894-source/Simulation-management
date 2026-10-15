Normalized meter-scale static model; 3736 triangles. Engine FBX roundtrip validates mesh/triangles/available textures and embeds exact current Runtime GLB 1024x1024 image bytes. Editable retains original-resolution packed textures. Original_Source is archival unchanged Tripo FBX; its source-scale/legacy texture paths are not the engine prefab. Use *_Engine.fbx or *_Runtime_1k.glb. No collider/LOD created. 

Formats:
- Editable.blend: local editable geometry/rig/actions, original-resolution packed + relative external Textures.
- Engine.fbx: normalized meters, +Y up / -Z forward, exact existing current-runtime texture bytes embedded (512 characters / 1024 props); FBX take names may have rig prefixes.
- Runtime GLB: exact existing web-game asset (512 characters / 1024 props).
- Original_Source: unchanged original FBX archival provenance. It may retain original source scale and old absolute texture paths; not the TA import choice.
- Textures: original resolution + separately extracted runtime images (maximum 1K; folder Runtime_1k denotes maximum, not all images exactly 1K).

Only current management scope is treated as required. Optional legacy characters/halves are reserve resources. No first-person player body/hands or combat/damage actions are required by the current camera-only gameplay.

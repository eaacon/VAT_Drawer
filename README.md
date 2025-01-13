# Blender VAT Drawer
(Work-in-progress)

## Features:
- Set animation start frame, end frame, step length.
- Draw Vertex Animation Textures (VATs) from any animation, cloth sim, soft body sim, rigid bodies, and even some geometry nodes setups.
- VATs that include multiple object's animations
- Export additional objects that wont be influenced by VAT in a single file.
- Export FBX or GLTF
- Export textures only
- Pack VATs as close to square as possible (Adjusting UVs to match WIP).

  Currently most reliable with rigidbody, cloth, soft bodies, and transform animations, without packing square, uses scene export image settings so turning off filmic of AgX is necessary for accuracy.

  VFX created using this tool here: https://youtu.be/j-KO_elnDqA?si=AK40dsyPBOUhSSNr

  Once tool is more stable will update README to make more sense, I wrote this at 3am.

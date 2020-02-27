# Blender Animation Retargeting

This addon enables the transfer of animations and poses from one rig to another.


## Installation
1. Download this repo as .zip
2. In Blender go to Edit > Preferences > Add-ons > Install...
3. Select the downloaded .zip
4. Enable the Add-on, which will appear in the list



## How to use
Assuming you have both your target and source armature in the scene, and have them aligned and scaled to match each other. 

*Note: The target's scale has to be (1, 1, 1), scale the source to fit the target*

![Both armatures in rest pose next to each other, scaled to be same height](https://manuelotto.com/files/retarget/setup.png)

1. Select your target armature and open the add-on panel on the right side of the 3D View (Rarget tab)
2. Now choose the source armature as 'Source' on the panel
3. It should say that there are no bone mappings, yet. Go ahead and click 'Create'.
4. Now map each relevant source bone to the corresponding target. Make sure to map every bone once, otherwise you'll get undefined behaviour.
5. Next you have to set up the rest pose alignment. Click on "Set up", then change the pose of your target armature in a way, that it optimally fits your source armatures rest pose. When done click 'Apply'. ![pose adjusted to fit source's rest pose](https://manuelotto.com/files/retarget/align.png)
6. The add-on will then automatically create drivers for each bone, and you should be good to go.

## Correction Features
### Foot / Hand Positions Correction
If there's significant 'foot-sliding' or odd arm movements, due to anatomical differences between your rigs, you can turn on:
- Correct Feet Position
- Correct Hands Position

You will be asked to specify the leg/foot, arm/hand bones respectively. 
This will create and IK bone setup for the specified limbs whereas the target positionfor the feet/hands is copied over from the source.
Additionally it will spawn a control empty cube, that allows you to transform the target position as shown in this gif:

![demonstration of the ik correction transform cube](https://manuelotto.com/files/retarget/ik_transform_control.gif)

### Root Bone Pivot Correction
Incase the pivot point of your target and sources' root bone is not very much aligned. (On a different height mainly), you can try to enable 'Correct Root Pivot'. This will prevent your character to wobble left/right when there's major hip movement.

![difference in root bone pivot location (even though the rigs are scaled to be same height)](https://manuelotto.com/files/retarget/pivot.png)

## Baking
For convenience you can bake the source's animation into an action for your target via the add-on. Since the target bones are driven by drivers, you can bake everything youself, if you want. Make sure the check 'Visual Keying', though.
Ignore the 'Batch Import & Bake' option. (It covers my personal needs)

*Important: After baking your animation, make sure to check 'Disable Drivers' to actually see the keyframes, otherwise the drivers will override any animation on the target.*

## Limitations

- Intended and tested for bipeds with similar anatomy only.
- Blender's IK system can be weird sometimes
- I created this add-on because I needed its functionality for my own projects, It's published out of courtesy, so don't expect major support
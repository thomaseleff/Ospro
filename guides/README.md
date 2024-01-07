# Build guides
The build guides provide instructions to make hardware and software modifications to the Gaggia Classic (Evo) Pro espresso machine. These guides include a list of the needed parts (including 3D printer files), tools, and step-by-step assembly instructions.

> [!CAUTION]
> The following guides are provided for informational purposes only. The publisher(s) of the guides assume(s) no responsibility for any personal or property damage, loss of functionality or warranty, or other consequences resulting from the use of the guides. Users proceed at their own risk and are advised to seek professional assistance.

## Table of contents

#### [Hardware](#hardware-guides)
- [Variable pressure controller](#variable-pressure-controller)
- [Water preheating coil](#temperature-pre-heating-coil)

#### [Software](#software-guides)
- [Ospro](#ospro-prototype)

# Hardware guides
Hardware guides cover modifications that involve changing the existing hardware or adding on additional hardware to the espresso machine without the need for software. This means that hardware modifications are a great place to start as they can be made individually without dependence on other hardware or software modifications.

## Variable pressure controller
The variable pressure controller provides manual pressure control via a rotary dial, allowing for full control over the current supplied to the pump throughout extraction. By adjusting the current, the flow rate is adjusted, allowing for a full range of extraction pressures from low pressure pre-infusion (1-3 bars) to 12 bars. Pressure control is vital for proper extraction of nuanced flavors and aromas throughout the brewing process.

### Parts
- 1 x 25 W 100 OHM high power wirewound rheostat
- 1 x 16 AWG 600 V wire (6 FT length)
- 1 x 1/4 IN PET expandable braided sleeving (22 IN length)
- 4 x Female 16 AWG disconnect
- 2 x Male 16 AWG disconnect
- 2 x 1/4 IN shrink wrap (1.5 IN length)
- 1 x [3D printed enclosure](https://cad.onshape.com/documents/64f241d8e2f6bf438afa5b67/w/5135805c6b87d0dba22b77a7/e/a455f75cacce987199a97961)
- 1 x [3D printed front end-cap](https://cad.onshape.com/documents/64f241d8e2f6bf438afa5b67/w/5135805c6b87d0dba22b77a7/e/b7d37d7233d42274cbf21a53)
- 1 x [3D printed rear end-cap](https://cad.onshape.com/documents/64f241d8e2f6bf438afa5b67/w/5135805c6b87d0dba22b77a7/e/9c09796ffe08f1e6f5b5e0ba)
- 8 x M2.5 x 4 MM screws

### Tools
- Wire stripper/cutter
- Wire crimper
- Screwdriver
- 9/16 IN hex wrench
- Lighter/heat gun

### Instructions
> [!WARNING]
> Prior to making any modifications, unplug the espresso machine power cable completely.

1. Cut the 16 AWG 600 V wire into three sections, 2 x 30 IN sections and 1 x 8 IN section, using the wire stripper/cutter.
2. Cut the 1/4 IN PET expandable braided sleeving into 1 x 22 IN section, burnishing the ends with the lighter/heat gun.
3. Holding the two wires together on one end, feed them through the 1/4 IN PET expandable braided sleeving. Feed the sleeving onto the wires until an equal amount of the wires is remaining at each end.
4. Thread two 1.5 IN sections of 1/4 IN shrink wrap onto the sleeved wire assembly. Fix one section of shrink wrap over each the end of the braided sleeving using the lighter/heat gun, securing it in place.
5. Strip 1/4 IN of wire insulation from both ends of each 30 IN wire as well as both ends of the 8 IN wire.
6. On each 30 IN wire, crimp a female 16 AWG disconnect to one end of the wire assembly and crimp a male 16 AWG disconnect on the other end using the wire crimper. Each wire should have the same type of disconnect on both ends.
7. On the 8 IN section, crimp a female 16 AWG disconnect on each end using the wire crimper.
8. Connect the 8 IN wire to the right wire of the sleeved cable assembly, creating one longer wire with the 8 IN section.
9. Remove the top hold-down nut from the shaft of the rheostat using the hex wrench, then insert the rheostat into the enclosure, pressing the rheostat through the holes in the top of the enclosure. Screw down the hold-down nut and tighten with the hex wrench.
10. Loosen the holding screw of the rheostat knob, then insert the knob onto the shaft of the rheostat. Align the holding screw with the flat knotch of the shaft. Once in place, tighten the holding screw to fix the knob in place with the screwdriver.
11. Thread the end of the shorter wire of the wire assembly with the female disconnect through the right hole of the rear end-plate. Thread the end of the longer wire of the wire assembly with the female disconnect through the center hole of the rear end-plate.
12. Holding the enclosure so that the terminals of the rheostat are facing away, connect the female disconnect of the shorter wire to the left-hand terminal of the rheostat. Connect the female disconnect of the longer wire to the center terminal of the rheostat.
13. Screw the front and rear end-plates to the enclosure with the 8 x M2.5 x 4 MM screws and screwdriver.
14. Unplug the espresso machine power cable.
15. Remove the top plate of the espresso machine.
16. Remove the screws holding the pump assembly to the bottom of the espresso machine enclosure (this is to allow more freedom of movement to manage the wires connected to the pump).
17. Move the espresso machine so that the back of the machine is facing away, then remove the left disconnect from the pump.
18. Attach the male disconnect of the shorter wire to the female disconnect of the wire that used to be attached to the pump.
19. Attach the female disconnect of the longer wire to the left terminal of the pump.
20. Screw down the pump assembly to the bottom of the espresso machine enclosure and replace the top plate of the espresso machine.
21. Plug back in the espresso machine power cable.
22. Turn on the espresso machine, then turn on the brew switch. While brewing, turn the rotary knob of the rheostat. As the knob is turned to the left, the flow of water should decrease. As the knob is turned to the right, the flow of water should increase.

## Water preheating coil
The water pre-heating coil provides an insulated, passively heated boiler intake water line that retains just over 3 oz of water within 10 ft of copper tubing. By passively heating the intake water to the boiler, the boiler is able to maintain a much more stable temperature. Overall, this yields a much more consistent brew temperature during extractions reducing the time between extractions.

### Parts
- 1 x 1/4 IN OD x 10 FT utility copper tubing
- 2 x 1/4 IN OD Compression x 1/4 IN FIP brass adapter fitting
- 2 x 1/8 IN Barb x 1/4 IN MIP brass adapter fitting
- 1 x High-temperature silicone foam, 12 IN x 12 IN, 1/4 IN thick, extra soft
- 1 x High-pressure reinforced silicone rubber tubing for food and beverage, 1/8 IN ID, 23/64 IN OD, 2 FT Length
- 4 x 5/16 - 5/8 IN stainless steel hose clamp
- 4 x 12 IN Zip-ties

### Tools
- Copper tubing cutter
- Tomato sauce jar
- Teflon tape
- Adjustable wrench
- 1/2 IN wrench
- Utility knife
- Screwdriver
- 4 MM hex key
- 5 MM hex key

### Instructions
> [!WARNING]
> Prior to making any modifications, unplug the espresso machine power cable completely.

1. Inspect the ends of the copper tubing, if either end is not perfectly round, use the copper tubing cutter to remove the damaged section.
2. Place one end of the copper tubing pointing away from you on a flat surface. Holding the tomato sauce jar horizontally on top of the copper tubing, gently wrap the copper tubing around the jar, rolling the jar towards you. Use the flat surface to guide the copper wire around the jar in small sections, carefully avoiding any kinks or crimps in the tubing.
3. Attach the 1/4 IN OD compression fitting to each end of the copper tubing coil. Wrap 3-4 layers of teflon tape around the adapter threads before tightening with the adjustable and 1/2 IN wrenches.
4. Attach the 1/8 IN barb fitting to each end of copper tubing coil. Wrap 3-4 layers of teflon tape around the adapter threads before tightening with the adjustable and 1/2 IN wrenches.
5. Make the boiler insulation template,
   - Print out the boiler insulation template
   - Tape the pages where indicated, cutting out the template following the solid line.
6. Secure the boiler insulation template to the high-temperature silicone foam sheet and trace along the edge of the template, transfering the template to the foam sheet. Mark the placement of through-holes. Cut along the marked line with the utility knife and poke through the foam with a screwdriver to create the through-holes. 
7. With the copper coil positioned vertically and the upper inlet positioned pointing away from you, wrap the silicone foam around the coil so that the square cutout of the silicone foam is at the bottom of the coil. Secure the silicone foam in place lightly with the zip-ties.
8. Unplug the espresso machine power cable.
9. Remove the top plate of the espresso machine.
10. Remove the wires connected to the brew and steam thermostats and the heating elements. Unscrew the ground bracket holding the fuse in place, moving the ground wire and fuse wire assembly to the side. Remove the wires connected to the front-panel rocker switches.
11. Remove the machine screws holding the boiler assembly to the espresso machine enclosure using the 4 MM hex key (this is to allow more freedom of movement to fit the copper coil and silicone foam around the boiler).
12. Remove the machine screws holding the steam wand assembly to the boiler using the 5 MM hex key.
13. Remove the machine screws holding the 3-way solenoid valve to the boiler using the 4 MM hex key.
14. Remove the espresso machine boiler from the espresso machine.
15. Remove the pink braided tubing from the inlet barb of the boiler.
16. Place the copper coil and silicone foam assembly over the top of the boiler. Rotate the square cutout so that it is positioned over the 3-way solenoid value outlet.
17. Press the 1 FT high-pressure reinforced silicone tubing onto the lower barb fitting of the copper coil, securing in place with a hose clamp, tightening with the screwdriver. Press the other end of the 1 FT high-pressure reinforced silicone tubing onto inlet barb of the boiler, securing in place with a hose clamp, tightening with the screwdriver.
18. Insert the boiler back into the espresso machine enclosure, reversing steps 11-13.
19. Press the pink braided tubing onto the upper barb fitting of the copper coil, securing in place with a hose clamp, tightening with the screwdriver.
20. Reinstall the ground wire bracket and fuse. Insert the top sheet of silicone foam, then reconnect the wires to the brew and steam thermostats and the heating elements. Reconnect the wires to the front-panel rocker switches.
21. Screw down the boiler assembly to the bottom of the espresso machine enclosure and replace the top plate of the espresso machine.
22. Plug back in the espresso machine power cable.
23. Turn on the espresso machine. Then, turn on the brew switch until water flows out of the grouphead.

# Software guides
Software guides cover modifications that involve changing the existing hardware as well as adding on additional hardware and software to the espresso machine.

## Ospro (prototype)
The main board contains the Raspberry Pi as well as the other core hardware required for the Ospro software application. The hardware below supports the following features,
- User-interface display
- Espresso extraction data tracking (temperature and pressure over-time) and storage
- Temperature control

### Parts
- 1 x Raspberry Pi 4 Model B
- 1 x SanDisk 16GB Ultra microSDHC UHS-I memory card with adapter
- 1 x Raspberry Pi official power supply
- 1 x 7 inch 1024x600 IPS, touchscreen display mini HDMI monitor
- 1 x Micro HDMI to mini HDMI cable
- 1 x SanDisk 16GB Ultra Fit USB 3.1 flash drive
- 1 x 40 pin GPIO T-Cobbler breakout board with ribbon cable
- 1 x K Type Thermocouple with M4 Thread
- 1 x Adafruit K-Type Thermocouple Amplifier - MAX31855
- 1 x Solid State Relay 40DA DC SSR
- 1 x 330 ohm resistor
- 1 x Blue LED
- 1 x Pressure Transducer 1/8"NPT Thread Stainless Steel (500 PSI)
- 1 x Adafruit 16-Bit ADC - 4 Channel with Programmable Gain Amplifier - ADS1115
- 1 x Adafruit 4-channel I2C-safe Bi-directional Logic Level Converter - BSS138
- 1 x Full size breadboard
- 3 x 2 Pin 5 MM PCB Mount Screw Terminal Block
- 1 x 8 x 10 1/8" thick acrylic sheet
- 1 x 3/4" x 10 ft roll of removable foam mounting tape
- 4 x 5 MM M2.5 standoffs and nuts
- 1 1/4 IN x 1/8 IN FIP brass reducing coupling fitting
- Various color solid core wire

### Tools
- Wire stripper/cutter
- Needle nose pliers
- Screwdriver
- Utility knife
- Drill and bits
- Teflon tape
- Thermal paste
- Adjustable wrench

### Instructions
> [!WARNING]
> Prior to making any modifications, unplug the espresso machine power cable completely.

1. Insert the T-cobbler, thermocouple amplifier (MAX31855), bi-directional logic level converter (BSS138), gain amplifier (ADS1115), blue LED and resistor into a full-size breadboard according to the following diagram.
![Breadboard part layout](/pcb-board/assets/main_board_prototype_parts.jpg)

2. Connect the components to the T-cobbler using the solid core wire. Cut sections of the wire slightly longer than each run, strip 1/8" of sleeving from each end, then create 90-degree bends using the needle nose pliers. Insert the wires into the breadboard according to the following diagram.
![Breadboard wiring layout](/pcb-board/assets/main_board_prototype.jpg)

3. Connect the Raspberry Pi to the T-cobbler using the 40 pin ribbon cable, ensuring that the pins on the Raspberry Pi are correctly connected. Improperly connecting the Raspberry Pi could damage the Pi itself and the parts.
4. Connect the k-type thermocouple to the screw terminals of the thermocouple amplifier (MAX31855) according to the silkscrean layout on the amplifier PCB.
5. Connect the red, green and black leads of the pressure transducer to the first, second and third screw terminals (starting on the left) of the PCB mounted screw terminal blocks.
6. Connect a wire to the fifth screw terminal (starting on the left) to the positive input terminal of the solid state relay. Connect a wire to the 6th screw terminal (starting on the left) to the negative input terminal of the solid state relay.
7. Place two strips of the foam adhesive tape to the back of the breadboard and adhere it to the surface of the acrylic sheet.
8. Holding the Raspberry Pi onto the surface of the acrylic sheet, mark each mounting holes position on the acrylic. Drill a hole through the acrylic on each mark. Secure the Raspberry Pi to the acrylic sheet using the 4 x 5 MM M2.5 standoffs and nuts.
9. Unplug the espresso machine power cable.
10. Remove the top plate of the espresso machine.
11. Remove the steam wand assembly. Attach the 1/4 IN x 1/8 IN FIP brass reducing coupling to the steam outlet. Wrap 3-4 layers of teflon tape around the adapter threads before tightening with the adjustable wrench.
12. Attach the pressure transducer to the reducing coupling. Wrap 3-4 layers of teflon tape around the threads before tightening with the adjustable wrench.
13. Remove the brew thermostat from the boiler. Add a small amount of thermal paste to the M4 threads of the thermocouple. Screw in the thermocouple where the brew thermostat used to be located on the boiler.
14. Attach the leads that used to be attached to the brew thermostat to the output terminals of the solid state relay.
15. Replace the top plate of the espresso machine.
16. Connect the 7 IN touchscreen display to the Raspberry Pi. Place the screen on top of the espresso machine.
17. Connect the 16 GB USB drive, a keyboard and mouse to the Raspberry Pi.
18. Plug in the Raspberry Pi power supply.
19. Update the Raspberry Pi operating system. Enable I2C and reboot.
20. Navigate to the 16 GB USB drive and run the following command,
```
git clone https://github.com/thomaseleff/Ospro.git
```
21. Install the Python library requirements from ```requirements_RPi.txt```.
22. Open and configure ```config.json``` within the ```~/config``` subfolder.
23. Plug back in the espresso machine power cable.
24. Run ```main.py```.
25. Once the user-interface displays, turn on the espresso machine.
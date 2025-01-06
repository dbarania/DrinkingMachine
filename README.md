## Project Plan
Our project consists of 3 seperate devices working together offering prestige experience of interactionless drink ordering. 

### Ordering thingy
Gestures based ordeing system, BLE TinyML Arduino with IMU on board will read, classify simple gestures and send the order to the system via Bluetooth
Ordering process is started with the press of a button to minimize power consumption. 

Steps:

1. Collect data from the board's IMU and send it to the computer
2. Train gesture classifier 
3. Deploy TinyML model on the Arduino
4. Set up BLE to send the results of the inference after confirming the order
5. Designing and developing proper electronic conections, battery pack and suitable container for everything.

### Vehicle waiter 

Camera powered line follower car delivering the drink from the machine to the customer.
It will be build of onboard computer (Raspberry Pi 3B+) and microcontroller (Probably Raspberry Pi pico) communicating via wireless protocol (I2C, SPI, UART)
THe computer will be connected to the main system via Bluetooth or WiFi.

Goals to accomplish in no particular order:
- Setting up reliable communication protocol between RPi and MCU allowing to send commands and data
- Accurate and efficient control scheme, managing motors -> movement of a vehicle.
- Camera based line following control inputs generation
- Bluetooth or WiFi communication with the main system
- Recognition of customers to deliver drinks
- Acceptable electronics circuit
- Design of the vehicle

#### Hardware needed
- [ ] 2 DC motors
- [ ] 2 H-bridges
- [ ] 2 encoders*
- [ ] 2 Rubber wheels
- [ ] 1 freerly moving wheel
- [ ] IR sensor
- [ ] Battery system
- [x] Webcamera 3 
- [x] Raspberry Pi
- [x] Microcontroller

### Drink mixing machine
Machine pouring drinks to the cup provided by a vehicle. It is controlled by a computer (Raspberry Pi 5).

Goals
 - Design of a drink container with level monitoring and solenoid valves to pour liquid.
 - Drink stirring mechanism (design and execution)
 - Drink pouring design
 - Order logic of pouring enough liquids combined
### Statistic collection (server)*
### Communications system

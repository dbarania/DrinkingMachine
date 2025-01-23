import time, asyncio
from bleak import BleakClient, BleakScanner, discover

mac_address = "3D:05:EA:3A:81:18"
#SERVICE_UUID = "1A0"
RESULT_UUID = "13012F01-F8C3-4F4A-A8F4-15CD926DA146"

async def run():
    print('Raspberry Pi 5 Central Service')
    print('Looking for Arduino Nano 33 BLE Sense Peripheral Device...')

    found = False
    devices = await discover()
    for d in devices:       
        if 'Arduino Nano 33 BLE Sense'in d.name:
            print('Found Arduino Nano 33 BLE Sense Peripheral')
            found = True
            async with BleakClient(d.address) as client:
                print(f'Connected to {d.address}')

                while True:
                    
                        result = await client.read_gatt_char(RESULT_UUID)
                        res_convert = int.from_bytes(result)

                        print(f"Movement detected: {res_convert}")

                        # await asyncio.sleep(1)


                # result = await client.read_gatt_char(RESULT_UUID)

                # print(f"Movement detected: {result}")
                 

    if not found:
        print('Could not find Arduino Nano 33 BLE Sense Peripheral')

while True:
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print('\nReceived Keyboard Interrupt')
    finally:
        print('...')
       
        print('\nRetrying...\n')

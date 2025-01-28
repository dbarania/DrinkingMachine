import time, asyncio
from bleak import BleakClient, BleakScanner

mac_address = "3D:05:EA:3A:81:18"
RESULT_UUID = "13012F01-F8C3-4F4A-A8F4-15CD926DA146"

async def run():
    print('Raspberry Pi 5 Central Service')
    print('Looking for Arduino Nano 33 BLE Sense Peripheral Device...')

    found = False
    while not found:
       
        devices = await BleakScanner.discover()
        for d in devices:
            if 'Arduino Nano 33 BLE Sense' in d.name:
                print('Found Arduino Nano 33 BLE Sense Peripheral')
                found = True
                async with BleakClient(d.address, timeout=30) as client:
                    print(f'Connected to {d.address}')
                    while found:
                        try:
                            result = await client.read_gatt_char(RESULT_UUID)
                            res_convert = result.decode('utf-8')
                            print(f"Movement detected: {res_convert}")
                        except Exception as e:
                            print(f'Could not read characteristic: {e}.')
                            found = False
                            break
       
        if not found:
            print("Retrying to find device...")
            await asyncio.sleep(2)  

    print('Device found and connected, starting data reading...')

loop = asyncio.get_event_loop()
while True:
    try:
        loop.create_task(run())
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()
        print('\nReceived Keyboard Interrupt')
    finally:
        print('...')
        print('\nRetrying...\n')


# import time, asyncio
# from bleak import BleakClient, BleakScanner, discover

# mac_address = "3D:05:EA:3A:81:18"
# #SERVICE_UUID = "1A0"
# RESULT_UUID = "13012F01-F8C3-4F4A-A8F4-15CD926DA146"

# async def run():
#     print('Raspberry Pi 5 Central Service')
#     print('Looking for Arduino Nano 33 BLE Sense Peripheral Device...')

#     found = False
#     devices = await BleakScanner.discover()
#     for d in devices:       
#         if 'Arduino Nano 33 BLE Sense'in d.name:
#             print('Found Arduino Nano 33 BLE Sense Peripheral')
#             found = True
#             async with BleakClient(d.address) as client:
#                 print(f'Connected to {d.address}')
            
#                 # result = await client.read_gatt_char(RESULT_UUID)
#                 # res_convert = int.from_bytes(result)

#                 # print(f"Movement detected: {res_convert}")

       
#                 # result = await client.read_gatt_char(RESULT_UUID)


#                 while True:
#                     # try:
#                         # await asyncio.sleep(1)
#                         result = await client.read_gatt_char(RESULT_UUID)
#                         res_convert = result.decode('utf-8')


#                         print(f"Movement detected: {res_convert}")
                        


#                     # except Exception as e:
#                     #     print(f'Could not read characteristic: {e}.')
#                     #     break
                
                
                 

#     if not found:
#         print('Could not find Arduino Nano 33 BLE Sense Peripheral')

# loop = asyncio.get_event_loop()
# while True:

#     try:
#         loop.create_task(run())
#         loop.run_forever()
        
#     except KeyboardInterrupt:
#         loop.stop()
#         print('\nReceived Keyboard Interrupt')
#     finally:
#         print('...')
       
#         print('\nRetrying...\n')
    

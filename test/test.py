from lib.test.python import network


def print_bits(arr: bytearray):
    full = bytearray(8)
    full[0 : len(arr)] = arr
    bytes = " ".join(["{0:08b}".format(byte) for byte in full])
    print(f"[ {bytes} ]")


message = network.test_message_CAR_STATUS(
    inverter_l=network.test_InverterStatus.ON,
    inverter_r=network.test_InverterStatus.ON,
    car_status=network.test_CarStatus.RUN,
)

print_bits(message.serialize())

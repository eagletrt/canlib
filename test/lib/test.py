from lib.test.python import network


def print_bits(arr: bytearray):
    full = bytearray(8)
    full[0 : len(arr)] = arr
    bytes = " ".join(["{0:08b}".format(byte) for byte in full])
    print(f"[ {bytes} ]")


message = network.message_CAR_STATUS(
    inverter_l=network.InverterStatus.ON,
    inverter_r=network.InverterStatus.ON,
    car_status=network.CarStatus.RUN,
)

print("CAR_STATUS", end=" ")
print_bits(message.serialize())

message = network.message_DAS_ERRORS(
    das_error=network.DasErrors.FSM
    | network.DasErrors.INVL_TOUT
    | network.DasErrors.PEDAL_IMPLAUSIBILITY,
)

print("DAS_ERRORS", end=" ")
print_bits(message.serialize())

message = network.message_SET_TS_STATUS(ts_status_set=network.Toggle.OFF)

print("SET_TS_STATUS", end=" ")
print_bits(message.serialize())

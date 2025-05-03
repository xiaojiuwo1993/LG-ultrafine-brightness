import usb.core
import usb.util
import os
import sys
from typing import List, Optional

# Constants and supported devices
LG_ID_Vendor: int = 0x43E
support_device: dict[int, str] = {
    0x9A63: "24MD4KL",
    0x9A70: "27MD5KL",
    0x9A40: "27MD5KA",
}


class Brightness:
    # Static constants for maximum and minimum brightness
    MAX_BRIGHTNESS: int = 0xD2F0  # Max brightness (54000)
    MIN_BRIGHTNESS: int = 0x0000  # Min brightness (0)

    def __init__(self) -> None:
        # Private member variable for brightness
        self._lg_brightness: int = 0

    @property
    def lg_brightness(self) -> int:
        return self._lg_brightness

    @lg_brightness.setter
    def lg_brightness(self, value: int) -> None:
        if Brightness.MIN_BRIGHTNESS <= value <= Brightness.MAX_BRIGHTNESS:
            self._lg_brightness = value
        else:
            raise ValueError(
                f"Brightness must be between {Brightness.MIN_BRIGHTNESS} and {Brightness.MAX_BRIGHTNESS}"
            )


class UltrafineDisplay:
    def __init__(self, lg_usb: usb.core.Device) -> None:
        self.lg_dev: usb.core.Device = lg_usb
        self.lg_iface: int = 1
        self.brightness_step: int = 5
        self.DisplayType: str = support_device.get(
            lg_usb.idProduct, "Unknown"  # type:ignore
        )

        # Detach kernel driver and set configuration
        if self.lg_dev.is_kernel_driver_active(self.lg_iface):
            self.lg_dev.detach_kernel_driver(self.lg_iface)
        # self.lg_dev.set_configuration()

    def __del__(self) -> None:
        self.LG_Close()

    def LG_Close(self) -> None:
        usb.util.dispose_resources(self.lg_dev)

    def get_brightness(self) -> int:
        try:
            data: List[int] = self.lg_dev.ctrl_transfer(  # type:ignore
                bmRequestType=0xA1,  # bmRequestType: Specifies the direction (IN/OUT), type, and recipient of the request
                bRequest=0x01,  # bRequest: The specific request to execute (e.g., GET_REPORT)
                wValue=(0x03 << 8)
                | 0,  # wValue: A combination of parameters (e.g., report type and ID)
                wIndex=self.lg_iface,  # wIndex: Typically the interface number
                data_or_wLength=8,  # data_or_wLength: The length of the data to transfer (or the data itself)
                timeout=None,  # timeout: Optional, default is none
            )
            return data[0] + (data[1] << 8)
        except Exception:
            return 0

    def set_brightness(self, val: int) -> None:
        try:
            data: List[int] = [
                val & 0x00FF,
                (val >> 8) & 0x00FF,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
            self.lg_dev.ctrl_transfer(0x21, 0x09, (0x03 << 8) | 0, self.lg_iface, data)
        except Exception as e:
            print(f"Error setting brightness: {e}")

    def get_brightness_level(self) -> int:
        brightness: int = self.get_brightness()
        return int((brightness / 54000) * 100)

    def set_brightness_level(self, level: int) -> None:
        brightness: int = int(level * 54000 / 100)
        self.set_brightness(brightness)

    def interactive(self) -> None:
        brightness_volume: int = self.get_brightness_level()

        while True:
            os.system("clear" if os.name != "nt" else "cls")  # Clear the screen
            print(f"Current brightness level: {brightness_volume}")
            print("Options:")
            print("  '+' or '=' - Increase brightness")
            print("  '-' or '_' - Decrease brightness")
            print("  'i'        - Set brightness from 0 to 100")
            print("  'm'        - Set max brightness")
            print("  'q'        - Quit")

            choice: str = input("Choose an option: ").strip().lower()

            if choice in ("+", "="):
                brightness_volume = min(brightness_volume + self.brightness_step, 100)
                self.set_brightness_level(brightness_volume)
            elif choice in ("-", "_"):
                brightness_volume = max(brightness_volume - self.brightness_step, 0)
                self.set_brightness_level(brightness_volume)
            elif choice == "i":
                try:
                    new_brightness: int = int(
                        input("Enter brightness (0-100): ").strip()
                    )
                    brightness_volume = max(0, min(100, new_brightness))
                    self.set_brightness_level(brightness_volume)
                except ValueError:
                    print("Invalid input. Please enter a number between 0 and 100.")
            elif choice == "m":
                self.set_brightness_level(100)
                brightness_volume = 100
            elif choice == "q":
                print("Exiting interactive mode.")
                break
            else:
                print("Invalid option. Please try again.")


def get_lg_ultrafine_usb_devices() -> List[usb.core.Device]:
    devs: Optional[List[usb.core.Device]] = usb.core.find(find_all=True)  # type:ignore
    assert devs
    lg_devs: List[usb.core.Device] = []
    for dev in devs:
        if (
            dev.idVendor == LG_ID_Vendor  # type:ignore
            and dev.idProduct in support_device  # type:ignore
        ):
            lg_devs.append(dev)
    return lg_devs


def manually_set_brightness(lg_devs: List[usb.core.Device]) -> None:
    while True:
        os.system("clear" if os.name != "nt" else "cls")  # Clear the screen
        print(f"Found {len(lg_devs)} UltraFine displays:")
        display_pool: List[UltrafineDisplay] = [
            UltrafineDisplay(dev) for dev in lg_devs
        ]

        for idx, display in enumerate(display_pool):
            print(
                f"{idx}: {display.DisplayType}, "
                f"Brightness: {display.get_brightness_level()}"
            )

        print("\nEnter the display number to adjust or 'q' to quit.")
        choice: str = input("Your choice: ").strip().lower()

        if choice == "q":
            print("Exiting manual brightness adjustment.")
            break

        if choice.isdigit():
            chosen_idx: int = int(choice)
            if 0 <= chosen_idx < len(display_pool):
                display_pool[chosen_idx].interactive()
            else:
                print(f"Invalid display number: {choice}. Please try again.")
        else:
            print("Invalid input. Please try again.")

        for display in display_pool:
            display.LG_Close()


def set_brightness_with_argv(lg_devs: List[usb.core.Device], input_volume: str) -> None:
    input_volume_int: int = max(0, min(100, int(input_volume)))
    for dev in lg_devs:
        display: UltrafineDisplay = UltrafineDisplay(dev)
        display.set_brightness_level(input_volume_int)
        print(f"Set brightness to {input_volume_int} for {display.DisplayType}")
        display.LG_Close()


if __name__ == "__main__":
    lg_devs: List[usb.core.Device] = get_lg_ultrafine_usb_devices()

    if not lg_devs:
        print("No LG UltraFine displays found. Please check the connection.")
        sys.exit(-1)

    if len(sys.argv) == 1:
        manually_set_brightness(lg_devs)
    elif len(sys.argv) == 2:
        set_brightness_with_argv(lg_devs, sys.argv[1])
    else:
        print("Invalid parameters")

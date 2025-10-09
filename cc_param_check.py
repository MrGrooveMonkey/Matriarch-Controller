from data.parameter_definitions import PARAMETERS
from ui.main_window import MatriarchMainWindow
from PyQt5.QtWidgets import QApplication
import sys

# Create app instance
app = QApplication(sys.argv)
window = MatriarchMainWindow()

# Find all CC parameters defined
cc_params = {pid: param.name for pid, param in PARAMETERS.items() if pid >= 101 and pid < 300}
print(f"\n=== CC Parameters Defined (101-299) ===")
print(f"Total: {len(cc_params)}")
for pid in sorted(cc_params.keys()):
    print(f"  {pid}: {cc_params[pid]}")

# Check which have widgets
print(f"\n=== CC Parameters WITH Widgets ===")
cc_with_widgets = [pid for pid in sorted(cc_params.keys()) if pid in window.parameter_widgets]
print(f"Total: {len(cc_with_widgets)}")
for pid in cc_with_widgets:
    print(f"  {pid}: {cc_params[pid]}")

print(f"\n=== CC Parameters WITHOUT Widgets ===")
cc_without_widgets = [pid for pid in sorted(cc_params.keys()) if pid not in window.parameter_widgets]
print(f"Total: {len(cc_without_widgets)}")
for pid in cc_without_widgets:
    print(f"  {pid}: {cc_params[pid]}")

# Also check current_values
print(f"\n=== CC Parameters in current_values ===")
cc_in_current = [pid for pid in sorted(cc_params.keys()) if pid in window.current_values]
print(f"Total: {len(cc_in_current)}")
for pid in cc_in_current:
    print(f"  {pid}: {cc_params[pid]} = {window.current_values[pid]}")
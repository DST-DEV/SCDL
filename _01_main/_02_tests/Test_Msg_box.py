#%% Self written class

import PyQt6.QtWidgets as QTW
from PyQt6.QtCore import Qt

class MsgDialog(QTW.QDialog):
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        
        # Set up label and button box
        self.label = QTW.QLabel(message, self)
        self.label.setWordWrap(True)  # Allow text to wrap for proper sizing
        self.buttonBox = QTW.QDialogButtonBox(
            QTW.QDialogButtonBox.StandardButton.Yes 
            | QTW.QDialogButtonBox.StandardButton.No,
            self)

        # Set up the layout
        layout = QTW.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        # Adjust size to fit content
        self.adjustSize()
        
        #Setup buttons and response variable
        self._response = False 
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.on_reject)
        
    def on_accept (self):
        self._response = True
        self.accept()
        
    def on_reject (self):
        self._response = False
        self.reject()
        

# Test the dialog
if __name__ == "__main__":
    import sys
    app = QTW.QApplication(sys.argv)
    message = "This is a r"
    dialog = MsgDialog(message)
    dialog.exec()



#%% Class from QtDesigner

# =============================================================================
# import PyQt6.QtWidgets as QTW
# from Msg_Dialog import Ui_MsgDialog
# 
# class MsgDialog (QTW.QDialog, Ui_MsgDialog):
#     def __init__(self, msg=""):
#         super(MsgDialog, self).__init__()
#         self.setupUi(self)
#         self.msg_lbl.setText(msg)
#         self.msg_lbl.adjustSize() 
#         
#         
#         self._response = False
#         
#         #Connect buttons
#         self.buttonBox.accepted.connect(self.accept_response)
#         self.buttonBox.rejected.connect(self.reject_response)
#         
#     def accept_response (self):
#         self._response = True
#         self.accept()
#         
#     def reject_response (self):
#         self._response = False
#         self.reject()
#         
# if __name__ == "__main__":
#     import sys
#     app = QTW.QApplication(sys.argv)
#     MsgDialog = MsgDialog()
#     MsgDialog.show()
#     sys.exit(app.exec())
# =============================================================================

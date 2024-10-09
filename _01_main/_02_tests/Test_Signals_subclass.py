#%%Selection
ver = 2

#%%Version 0
if ver == 0:
    import sys
    import time
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel
    from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject, pyqtSlot
    
    # A class for emitting signals (since QRunnable does not support signals directly)
    class WorkerSignals(QObject):
        progress_updated = pyqtSignal(int)  # Signal to update progress bar
    
    # Worker class for running a function in a separate thread
    class Worker(QRunnable):
        def __init__(self, fn, *args, **kwargs):
            super(Worker, self).__init__()
            self.fn = fn  # Store the function to execute
            self.args = args  # Arguments for the function
            self.kwargs = kwargs  # Keyword arguments for the function
            self.signals = WorkerSignals()  # Use a separate object to handle signals
    
        @pyqtSlot()
        def run(self):
            """Run the function with the provided arguments."""
            self.fn(*self.args, **self.kwargs)
    
        def emit_progress(self, value):
            """Emit progress signal to update progress bar."""
            self.signals.progress_updated.emit(value)
    
    # A sample class with a long-running function to be executed in the background
    class SomeClass:
        def long_running_task(self, update_progress_callback):
            """A function that performs some work and reports progress."""
            for i in range(101):
                time.sleep(0.05)  # Simulate a long task
                update_progress_callback(i)  # Report progress
    
    # Main window with progress bar
    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
            
            # # Create a thread pool
            self.threadpool = QThreadPool()
            
            # Instance of another class containing the long-running function
            self.some_class = SomeClass()
            
            # Set up GUI components
            self.init_ui()
    
    
        def init_ui(self):
            """Initialize the user interface."""
            layout = QVBoxLayout()
    
            self.label = QLabel("Progress:")
            layout.addWidget(self.label)
    
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.progress_bar.setValue(0)  # Start with 0% progress
            layout.addWidget(self.progress_bar)
    
            self.start_button = QPushButton("Start Task", self)
            self.start_button.clicked.connect(lambda: self.run_fcn_thread(self.some_class.long_running_task)())
    
            # self.start_button.clicked.connect(self.run_fcn_thread(self.some_class.long_running_task))
            # self.start_button.clicked.connect(self.start_task)
            layout.addWidget(self.start_button)
    
            self.setLayout(layout)
            self.setWindowTitle('Progress Bar with Flexible Worker (QRunnable)')
            self.resize(300, 150)
    
        def start_task(self):
            """Start the worker to run the function from another class."""
            # Create a worker to run 'long_running_task' from 'SomeClass'
            worker = Worker(self.some_class.long_running_task, self.update_progress)
            worker.signals.progress_updated.connect(self.update_progress)  # Connect progress updates to the progress bar
    
            # Start the worker using QThreadPool
            self.thread_pool.start(worker)
        
        def run_fcn_thread (self, fcn):
            threadpool = self.threadpool
            
            def run_thread(self):
                worker = Worker(fcn, self.update_progress) # Any other args, kwargs are passed to the run function
                worker.signals.progress_updated.connect(self.update_progress)
                
                # Execute
                threadpool.start(worker)
            return run_thread
        
        def update_progress(self, value):
            """Update the progress bar with the current progress value."""
            self.progress_bar.setValue(value)
    
    # PyQt application setup
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


#%% Version 1
if ver == 1:
    import sys
    import time
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel
    from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject, pyqtSlot
    
    # A class for emitting signals (since QRunnable does not support signals directly)
    class WorkerSignals(QObject):
        progress_updated = pyqtSignal(int)  # Signal to update progress bar
    
    # Worker class for running a function in a separate thread
    class Worker(QRunnable):
        def __init__(self, fn, *args, **kwargs):
            super(Worker, self).__init__()
            self.fn = fn  # Store the function to execute
            self.args = args  # Arguments for the function
            self.kwargs = kwargs  # Keyword arguments for the function
            self.signals = WorkerSignals()  # Use a separate object to handle signals
    
        @pyqtSlot()
        def run(self):
            """Run the function with the provided arguments."""
            self.fn(*self.args, **self.kwargs)
    
        def emit_progress(self, value):
            """Emit progress signal to update progress bar."""
            self.signals.progress_updated.emit(value)
    
    # A sample class with a long-running function to be executed in the background
    class SomeClass:
        def long_running_task(self, update_progress_callback):
            """A function that performs some work and reports progress."""
            for i in range(101):
                time.sleep(0.05)  # Simulate a long task
                update_progress_callback(i)  # Report progress
    
    # Main window with progress bar
    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
    
            # Set up GUI components
            self.init_ui()
    
            # Instance of another class containing the long-running function
            self.some_class = SomeClass()
    
            # Create a thread pool
            self.thread_pool = QThreadPool()
    
        def init_ui(self):
            """Initialize the user interface."""
            layout = QVBoxLayout()
    
            self.label = QLabel("Progress:")
            layout.addWidget(self.label)
    
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.progress_bar.setValue(0)  # Start with 0% progress
            layout.addWidget(self.progress_bar)
    
            self.start_button = QPushButton("Start Task", self)
            self.start_button.clicked.connect(self.start_task)
            layout.addWidget(self.start_button)
    
            self.setLayout(layout)
            self.setWindowTitle('Progress Bar with Flexible Worker (QRunnable)')
            self.resize(300, 150)
    
        def start_task(self):
            """Start the worker to run the function from another class."""
            # Create a worker to run 'long_running_task' from 'SomeClass'
            worker = Worker(self.some_class.long_running_task, self.update_progress)
            worker.signals.progress_updated.connect(self.update_progress)  # Connect progress updates to the progress bar
    
            # Start the worker using QThreadPool
            self.thread_pool.start(worker)
    
        def update_progress(self, value):
            """Update the progress bar with the current progress value."""
            self.progress_bar.setValue(value)
    
    # PyQt application setup
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

#%% Version 2
if ver == 2:
    import sys
    import time
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel
    from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject, pyqtSlot
    
    # A class for emitting signals (since QRunnable does not support signals directly)
    class WorkerSignals(QObject):
        progress_updated = pyqtSignal(int)  # Signal to update progress bar
    
    # Worker class for running a function in a separate thread
    class Worker(QRunnable):
        def __init__(self, fn, *args, **kwargs):
            super(Worker, self).__init__()
            self.fn = fn  # Store the function to execute
            self.args = args  # Arguments for the function
            self.kwargs = kwargs  # Keyword arguments for the function
            self.signals = WorkerSignals()  # Use a separate object to handle signals
    
        @pyqtSlot()
        def run(self):
            """Run the function with the provided arguments."""
            # Execute the function with the provided arguments
            self.fn(self.emit_progress, *self.args, **self.kwargs)
            # self.fn(*self.args, **self.kwargs)
    
        def emit_progress(self, value):
            """Emit progress signal to update progress bar."""
            self.signals.progress_updated.emit(value)
    
    # A sample class with multiple functions to be executed in the background
    class SomeClass:
        def long_running_task(self, update_progress_callback):
            """Simulates a long-running task and updates progress."""
            self.helper_task(update_progress_callback)
            
            # for i in range(101):
            #     time.sleep(0.05)  # Simulate long task
            #     update_progress_callback(i)  # Report progress
        
        def helper_task(self, update_progress_callback):
            for i in range(101):
                time.sleep(0.05)  # Simulate long task
                update_progress_callback(i)  # Report progress
        
        def another_task(self, update_progress_callback):
            """Another example of a long-running task."""
            for i in range(101):
                time.sleep(0.03)  # Simulate a different task
                update_progress_callback(i)  # Report progress
    
    # Main window with progress bar
    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
    
            # Set up GUI components
            self.init_ui()
    
            # Instance of another class containing multiple long-running functions
            self.some_class = SomeClass()
    
            # Create a thread pool
            self.thread_pool = QThreadPool()
    
        def init_ui(self):
            """Initialize the user interface."""
            layout = QVBoxLayout()
    
            self.label = QLabel("Progress:")
            layout.addWidget(self.label)
    
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.progress_bar.setValue(0)  # Start with 0% progress
            layout.addWidget(self.progress_bar)
    
            # Button to start task 1
            self.start_button1 = QPushButton("Start Task 1", self)
            self.start_button1.clicked.connect(lambda: self.run_fcn_thread(self.long_running_task))
            layout.addWidget(self.start_button1)
    
            # Button to start task 2
            self.start_button2 = QPushButton("Start Task 2", self)
            # self.start_button2.clicked.connect(self.start_task_2)
            layout.addWidget(self.start_button2)
    
            self.setLayout(layout)
            self.setWindowTitle('Progress Bar with Flexible Worker (QRunnable)')
            self.resize(300, 200)
    
        # def start_task_1(self):
        #     """Start the worker to run 'long_running_task' from SomeClass."""
        #     worker = Worker(self.some_class.long_running_task)
        #     worker.signals.progress_updated.connect(self.update_progress)
        #     self.thread_pool.start(worker)
    
        # def start_task_2(self):
        #     """Start the worker to run 'another_task' from SomeClass."""
        #     worker = Worker(fn = self.some_class.another_task)
        #     worker.signals.progress_updated.connect(self.update_progress)
        #     self.thread_pool.start(worker)
        
        def long_running_task(self, update_progress_callback):
            self.some_class.long_running_task (update_progress_callback)
            
        def run_fcn_thread(self, fcn):
            """Start the worker to run 'long_running_task' from SomeClass."""
            worker = Worker(fcn)
            worker.signals.progress_updated.connect(self.update_progress)
            self.thread_pool.start(worker)
            
        def update_progress(self, value):
            """Update the progress bar with the current progress value."""
            self.progress_bar.setValue(value)
    
    # PyQt application setup
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

#%% Version 3
if ver==3:
    import sys
    import time
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel
    from PyQt6.QtCore import Qt, QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot
    
    # Worker class that can run a given function in a separate thread
    class Worker(QObject, QRunnable):
        progress_updated = pyqtSignal(int)  # Signal to update progress
    
        def __init__(self, fn, *args, **kwargs):
            QObject.__init__(self)  # Initialize QObject
            QRunnable.__init__(self)  # Initialize QRunnable
            self.fn = fn  # Function to execute
            self.args = args  # Positional arguments for the function
            self.kwargs = kwargs  # Keyword arguments for the function
    
        @pyqtSlot()
        def run(self):
            """Execute the function and update progress."""
            try:
                self.fn(self.emit_progress, *self.args, **self.kwargs)
            except Exception as e:
                print(f"An error occurred: {e}")
    
        def emit_progress(self, value):
            """Emit the progress signal."""
            self.progress_updated.emit(value)
    
    # Class containing long-running tasks
    class SomeClass:
        def long_running_task(self, update_progress_callback):
            """Simulate a long-running task."""
            for i in range(51):  # Loop from 0 to 50
                time.sleep(0.05)  # Simulate work
                progress = int((i / 50) * 100)
                update_progress_callback(progress)  # Report progress
                self.helper_task(i, update_progress_callback)  # Call nested function
    
        def helper_task(self, i, update_progress_callback):
            """A helper function called within the long-running task."""
            time.sleep(0.02)  # Simulate additional work
            helper_progress = int((i / 50) * 100) + 1  # Offset progress
            update_progress_callback(helper_progress)
    
    # Main window of the application
    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.init_ui()  # Initialize the user interface
            self.some_class = SomeClass()  # Instance of SomeClass
            self.thread_pool = QThreadPool()  # Create a thread pool
    
        def init_ui(self):
            """Setup the user interface."""
            layout = QVBoxLayout()
    
            self.label = QLabel("Progress:")
            layout.addWidget(self.label)
    
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.progress_bar.setValue(0)  # Start at 0% progress
            layout.addWidget(self.progress_bar)
    
            # Button to start the long-running task
            self.start_button = QPushButton("Start Long Running Task", self)
            self.start_button.clicked.connect(self.start_long_running_task)
            layout.addWidget(self.start_button)
    
            self.setLayout(layout)
            self.setWindowTitle('Progress Bar with Nested Function Updates')
            self.resize(400, 200)
    
        def start_long_running_task(self):
            """Start the worker to run the long-running task."""
            worker = Worker(self.some_class.long_running_task)
            worker.progress_updated.connect(self.update_progress)  # Connect the signal
            self.thread_pool.start(worker)  # Start the worker thread
    
        def update_progress(self, value):
            """Update the progress bar."""
            if value > 100:
                value = 100
            self.progress_bar.setValue(value)
    
    # Run the application
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

    

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
            self.start_button1.clicked.connect(self.start_task_1)
            layout.addWidget(self.start_button1)
    
            # Button to start task 2
            self.start_button2 = QPushButton("Start Task 2", self)
            self.start_button2.clicked.connect(self.start_task_2)
            layout.addWidget(self.start_button2)
    
            self.setLayout(layout)
            self.setWindowTitle('Progress Bar with Flexible Worker (QRunnable)')
            self.resize(300, 200)
    
        def start_task_1(self):
            """Start the worker to run 'long_running_task' from SomeClass."""
            worker = Worker(self.some_class.long_running_task)
            worker.signals.progress_updated.connect(self.update_progress)
            self.thread_pool.start(worker)
    
        def start_task_2(self):
            """Start the worker to run 'another_task' from SomeClass."""
            worker = Worker(fn = self.some_class.another_task)
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



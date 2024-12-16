# Tobii Glasses 3 Server

This project serves as a server for streaming real-time data from **Tobii Glasses 3** and forwarding it to Unity. It uses the **Tobii Glasses 3 Python library**.

---

### Requirements
- Python 3.10
- If you have another version of Python, create a virtual environment:
  1. Install Python 3.10.
  2. Navigate to your project directory:
     ```
     cd /path/to/project
     ```
  3. Create the virtual environment:
     ```
     py -3.10 -m venv venv
     ```
  4. Activate it:
     - On Windows:
       ```
       venv\Scripts\activate
       ```

- If you haven't already, clone this [Unity project](https://github.com/lagenuina/UnityTobiiGlasses3.git).

### Install Dependencies
To install the required dependencies, run:
```
pip install .
```
```
pip install ".[test, examples, example-app]"
```

### Run the project

- Connect Tobii Pro Glasses 3 to Wi-Fi.

- Run the script
    ```
    python src/sendgazedata.py
    ```

This script connects to Tobii Glasses 3 to stream real-time gaze and video data. It sends **gaze information** *(pixel coordinates, eyes origin, direction and pupils diameter)* via TCP to Unity.
Streams **camera feed with gaze fixation** via UDP.
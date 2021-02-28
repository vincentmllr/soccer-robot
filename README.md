# Robot Lewandowski

Software for Anki Vector to play soccer.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

Python 3.7

### Soccerfield Dimensions

- 1000 mm x 1500 mm
- Goal width: 200 mm
- Start Position: x: 500; y: 500


### Installing

To install all additional modules needed

```
pip install -r requirements.txt
```

## Running the tests

The individual modules can be tested by running them directly.

## Deployment

1. run main.py
2. Put Vector on its start position
3. Activate the desired functions in the submenus (e.g. ball detection, marker detection)
4. Adjust the HSV color range for your lighting situation
5. Press enter to start the EnvironmentViewer
5. Press enter again to start the game

## Built With

* [OpenCV](https://github.com/opencv/opencv) - Used to detect the ball
* [Azure Custom Vision](https://docs.microsoft.com/de-de/azure/cognitive-services/custom-vision-service/) - Used to detect opponent Vectors
* [Pygame](https://github.com/pygame/) - Used for the map
* [Anki Vector API](https://developer.anki.com/vector/docs/index.html) - Used to send commands to Vector


## Authors

* **Vincent Müller** 
* **Philipp Binder** 
* **Tim Fischer** 

ESPHome keypad (work in progress).

It works in combination with appdemon to process key presses as well as Nuki codes.

You may also use it to switch your Home Assitant home alarm.

It is intended to be used with more than one keypad so each one may have its own code and key configuration. Thus, minimal configuration for each keypad is needed as common code is shared via includes. 

It requires Keypad_I2C library to function properly.

So, copy Keypad_I2C directory to every keypad lib directory.

It also includes some pcb prototype designs and pictures.

Let me know how responsive your keypad ends up as one of the issues you may encounter is a certain lack in key responsiveness due to ESPHome sensors update. 

Try it out and let me know!
int serValue = 0;
int serData[10];
int controlM = 0;
// Button values are reversed because of pullup resistors
int pedalUp = 1;
int pedalDown = 0;
boolean leftPedalWasDown = false;
boolean rightPedalWasDown = false;

void setup() {  
  //Setup mouse buttons
  pinMode(2,INPUT_PULLUP);
  pinMode(3,INPUT_PULLUP);
  Serial1.setTimeout(10);
  Serial.setTimeout(10);

  //while (!Serial1) {
    //; // wait for serial port to connect. Needed for Leonardo only
  //}
  delay(3000);
  
  //Serial1.setTimeout(1);
  Serial1.begin(57600);
  Serial.begin(57600);
  Mouse.begin();

  for(int i = 0; i<500; i++){
    delay(5);
    Mouse.move(absMax(-25, 1), absMax(-25, 1), 0);
  }
  
  Serial1.println("Starting mouse emulation...");
  delay(2000);
  
  Serial1.println("Starting mouse emulation...");
}

void loop() {
  int ctrlCode = 0;
  int xCarryOver = 0;
  int yCarryOver = 0;
  int maxMove = 100;

  // Get initial value
  while(true) {
    while (xCarryOver != 0 || yCarryOver !=0){
      int x = absMax(xCarryOver, maxMove);
      int y = absMax(yCarryOver, maxMove);
      
      Mouse.move(x, y);
      
      xCarryOver -= x;
      yCarryOver -= y;
    }
    
    // Todo: turn left and right click logic into a single reusable function that takes previous state and pedal read function pointer
    if(!leftPedalWasDown){
      if(readLeftPedal() == pedalDown){
        delay(250);
      
        if(readLeftPedal() == pedalUp){
          logger("Left button click.");
          // A quick release is interpreted as a click
          Mouse.click();
        } else {
          logger("Left button hold.");
          Mouse.press();
          leftPedalWasDown = true;
        }  
      }
      
    } else {
      if(readLeftPedal() == pedalUp) {
        logger("Left button release");
        Mouse.release();
        leftPedalWasDown = false;
      }
    }
    
    if(!rightPedalWasDown){
      if(readRightPedal() == pedalDown){
        delay(300);
      
        if(readRightPedal() == pedalUp){
          logger("Right button click.");
          // A quick release is interpreted as a click
          Mouse.click(MOUSE_RIGHT);
        } else {
          logger("Right button hold.");
          Mouse.press(MOUSE_RIGHT);
          rightPedalWasDown = true;
        }  
      }
      
    } else {
      if(readRightPedal() == pedalUp) {
        logger("Rigth button release.");
        Mouse.release(MOUSE_RIGHT);
        rightPedalWasDown = false;
      }
    }
   
    
    if (Serial1.find("c")) {
      // We've received the start of a control code
      ctrlCode = Serial1.parseInt();
      
      switch (ctrlCode) {
        case 0:
          // Request for device info
         Serial1.println("hm0.0.1");
          break;
        case 1:
          // Received code to move mouse
          xCarryOver += Serial1.parseInt();
          yCarryOver += Serial1.parseInt();
          break;
        case 2:
          maxMove = Serial1.parseInt();
          break;
        case 3:
          //Serial1.println("echo");
          //print out the value of the pushbutton
          Serial1.println();
          break;
        default: 
          // if nothing else matches, do the default
          // default is optional
        break;
      } 
    } else {
        //Serial1.println("No command received.");
    }        
  }
}

void logger(String message) {
  Serial.println(message);
  
  
}

int readLeftPedal() {
  return digitalRead(2);
}

int readRightPedal() {
  return digitalRead(3);
}

int absMax(int val, int maxVal) {
  int mag = abs(val);
  
  if (mag > maxVal) {
    mag = maxVal;
  }
  
  if (val < 0) {
    return mag * -1; 
  } else {
    return mag;   
  }
 
}

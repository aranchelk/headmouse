int serValue = 0;
int serData[10];
int controlM = 0;

void setup() {                
  //while (!Serial) {
    //; // wait for serial port to connect. Needed for Leonardo only
  //}
  delay(3000);
  
  //Serial.setTimeout(1);
  Serial.begin(57600);
  Mouse.begin();

  for(int i = 0; i<500; i++){
    delay(5);
    Mouse.move(absMax(-25, 1), absMax(-25, 1), 0);
  }
}

void loop() {
  int ctrlCode = 0;
  int xCarryOver = 0;
  int yCarryOver = 0;
  int maxMove = 100;

  // Get initial value
  while(true) {
    
    while (xCarryOver != 0 || yCarryOver !=0) {
      int x = absMax(xCarryOver, maxMove);
      int y = absMax(yCarryOver, maxMove);
      
      Mouse.move(x, y);
      
      xCarryOver -= x;
      yCarryOver -= y;
    }
    
    
    if (Serial.find("c")) {
      // We've received the start of a control code
      ctrlCode = Serial.parseInt();
        
      if (ctrlCode == 1) {
        // Received code to move mouse
        
        xCarryOver += Serial.parseInt();
        yCarryOver += Serial.parseInt();
      }
      
      if (ctrlCode == 2) {
        maxMove = Serial.parseInt();
      }
      
    }
              
  }
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

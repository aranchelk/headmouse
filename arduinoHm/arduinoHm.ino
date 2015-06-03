int serValue = 0;
int serData[10];
int controlM = 0;

void setup() {                
  //while (!Serial1) {
    //; // wait for serial port to connect. Needed for Leonardo only
  //}
  delay(3000);
  
  //Serial1.setTimeout(1);
  Serial1.begin(57600);
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
    
    
    if (Serial1.find("c")) {
      // We've received the start of a control code
      ctrlCode = Serial1.parseInt();
      
      if (ctrlCode == 0) {
        // Request for device info
        Serial1.println("hm0.0.1");
      }
        
      if (ctrlCode == 1) {
        // Received code to move mouse
        
        xCarryOver += Serial1.parseInt();
        yCarryOver += Serial1.parseInt();
      }
      
      if (ctrlCode == 2) {
        maxMove = Serial1.parseInt();
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

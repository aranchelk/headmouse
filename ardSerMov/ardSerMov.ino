int serValue = 0;
int serData[10];
int controlM = 0;

void setup() {                
  delay(3000);
  Serial.begin(9600);
  Mouse.begin();
}

void loop() {
  if (Serial.available() > 0) {
    //We're parsing serial into integers
    //Values greater than 32000 are control messages, less are data
    // Get initial value
    
    if(controlM == 0 ){
      serValue = Serial.parseInt();
    }
    
    if(serValue == 32001){
      //Serial.println("Break.");
      controlM = 0;
    }
    else if(serValue == 32100){
      //Serial.println("Mouse Move");
      int x = Serial.parseInt();
      int y = Serial.parseInt();

      mouseMove(x, y);
    }
    else{
      //Serial.println("Unknown control message.");
      controlM = 0;
    }
  }
}

void mouseMove(int x, int y){
 
    //Serial.println("Values for x and y:");
    //Serial.print(x);
    //Serial.println("");
    //Serial.print(y);
    //Serial.println("");
    Mouse.move(x, y, 0);
  
}

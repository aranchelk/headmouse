int serValue = 0;
int serData[10];
int controlM = 0;

void setup() {                
  delay(3000);
  Serial1.begin(9600);
  Mouse.begin();
  for(int i = 0; i<100; i++){
    delay(5);
    Mouse.move(1,1,0);
  }
}

void loop() {
  if (Serial1.available() > 0) {
    //We're parsing serial into integers
    //Values greater than 32000 are control messages, less are data
    // Get initial value
    
    if(controlM == 0 ){
      serValue = Serial1.parseInt();
    }
    
    if(serValue == 32001){
      //Serial1.println("Break.");
      controlM = 0;
    }
    else if(serValue == 32100){
      //Serial1.println("Mouse Move");
      int x = Serial1.parseInt();
      int y = Serial1.parseInt();

      mouseMove(x, y);
    }
    else{
      //Serial1.println("Unknown control message.");
      controlM = 0;
    }
  }
}

void mouseMove(int x, int y){
 
    //Serial1.println("Values for x and y:");
    //Serial1.print(x);
    //Serial1.println("");
    //Serial1.print(y);
    //Serial1.println("");
    Mouse.move(x, y, 0);
  
}

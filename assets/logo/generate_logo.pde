float s = 0;
float x = 0;

void setup() {
  size(342, 174);
  frameRate(10);
}

void draw() {
  background(#e5e5e5);
  translate(width/2, height/2);
  rotate(QUARTER_PI);

  // Ellipse forming the "bean"
  noFill();
  stroke(#e5e5e5);
  strokeWeight(7.5);
  fill(#3a7ebf);
  ellipse(0, 0, width/1.9, height/1.36);

  // Animated line
  x += 0.1;
  s = sin(x)*15;
  stroke(#e5e5e5);
  noFill();
  bezier(148, 4, s, s, -s, -s, -148, -4);

  // Restore the section below to save each frame as a .png in a new folder, "output"
  // you will need to first save this sketch.

  //saveFrame("output/frame###.png");

  //if (frameCount == 63) {
  //  exit();
  //}

  //The onboard "Movie Maker" tool can then be used to compile the .png's as an animated
  //GIF. Be sure to set Framerate to 10, Compression to Animated GIF (Loop), and check
  //same size as originals.
}

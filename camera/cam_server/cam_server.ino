#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>
 
const char* WIFI_SSID = "";
const char* WIFI_PASS = "";
 
WebServer server(80);
 
static auto resolution = esp32cam::Resolution::find(350, 530);

void serveJpg()
{
  auto frame = esp32cam::capture();
  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL");
    server.send(503, "", "");
    return;
  }
  Serial.printf("CAPTURE OK");
 
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client);
}
 

void handleJpg()
{
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("RESOLUTION SETUP FAILED");
  }
  serveJpg();
}
 
 
void  setup(){
  Serial.begin(115200);
  Serial.println();
  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(resolution);
    cfg.setBufferCount(2);
    cfg.setJpeg(80);
 
    Serial.println(Camera.begin(cfg) ? "CAMERA OK" : "CAMERA FAIL");
  }

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  Serial.print("http://");
  Serial.println(WiFi.localIP());
  Serial.println("/image.jpg");
 
  server.on("/image.jpg", handleJpg);
  server.begin();
}
 
void loop()
{
  server.handleClient();
}
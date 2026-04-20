#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>

const char* WIFI_SSID = "Mohamed's S24 Ultra";
const char* WIFI_PASS = "11111111";

WebServer server(80);

static auto hiRes = esp32cam::Resolution::find(800, 600);

void handleStream() {
  WiFiClient client = server.client();

  // Send multipart header — connection stays open
  String response =
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
    "Cache-Control: no-cache\r\n"
    "Connection: keep-alive\r\n\r\n";
  client.print(response);

  while (client.connected()) {
    auto frame = esp32cam::capture();
    if (frame == nullptr) {
      Serial.println("Capture fail");
      continue;
    }

    // Each frame is its own MIME part
    client.printf(
      "--frame\r\n"
      "Content-Type: image/jpeg\r\n"
      "Content-Length: %u\r\n\r\n",
      (unsigned)frame->size()
    );
    frame->writeTo(client);
    client.print("\r\n");  // part separator

    delay(0);  // yield to RTOS / watchdog
  }
}

void setup() {
  Serial.begin(115200);

  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(hiRes);
    cfg.setBufferCount(2);
    cfg.setJpeg(80);
    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");
  }

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  Serial.print("Stream: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/stream");

  server.on("/stream", handleStream);
  server.begin();
}

void loop() {
  server.handleClient();
}
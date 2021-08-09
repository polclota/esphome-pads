#define HOMEASSISTANT
#include <Keypad_I2C.h>

const auto buzzer_ms = 100;

const byte n_rows = 4;
const byte n_cols = 4;
bool arm_launch = false;
bool choose = false;

char keys[n_rows][n_cols] = {
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'}};

byte rowPins[n_rows] = {0, 1, 2, 3};
byte colPins[n_cols] = {4, 5, 6, 7};

Keypad_I2C myKeypad = Keypad_I2C(makeKeymap(keys), rowPins, colPins, n_rows, n_cols, 0x20);

std::string swOnState(KeyState kpadState)
{
  switch (kpadState)
  {
  case IDLE:
    return "IDLE";
    break;
  case PRESSED:
    return "PRESSED";
    break;
  case HOLD:
    return "HOLD";
    break;
  case RELEASED:
    return "RELEASED";
    break;
  } // end switch-case
  return "";
} // end switch on state function

void buzzer_off()
{
  id(buzzer).turn_off();
}

void buzzer_on()
{
  id(buzzer_s_on).execute();
  // id(buzzer).turn_on();
  // id(buzzer).set_level(50);
  delay(buzzer_ms);
  buzzer_off();
}

void turn_off_choose() // turn off choose / options screen
{
  static auto c = 0;
  if (choose || id(options))
  {
    c++;
    if (c > 15)
    {
      c = 0;
      choose = false;
      id(options) = false;
      id(password_str) = "";
      id(password_str_old) = "";
    }
  }
}

void arm_alarm()
{
  if (arm_launch)
  {
    id(arm_delay_p).show();
    id(my_display).update();
    id(arm_delay)--;
    if (id(arm_delay) == 0)
    {
      if (id(key) == "A")
        id(set_alarm_night).execute();
      else if (id(key) == "B")
        id(set_alarm_home).execute();
      else if (id(key) == "C")
        id(set_alarm_away).execute();
      id(arm_delay) = id(arm_delay_max);
      arm_launch = false;
      choose = false;
    }
  }
}

void options_service(std::string text)
{
  ESP_LOGI("options_service", "text, '%s'", text.c_str());
  std::string opt = "OPTIONS*";
  id(options) = text.find(opt) == 0;
  id(message_txt) = text.c_str();
  ESP_LOGI("options_service", "message_txt, '%s'", id(message_txt).c_str());
  id(msg_p).show();
  id(my_display).update();
  id(my_interval) = 0;
  id(codeT).publish_state("");
  if (!id(options)) // delete all previous records
  {
    id(password_str) = "";
    id(password_str_old) = "";
    choose = false;
    id(output_key).publish_state("");
  }
}

void text_sensor_key_plus()
{
  std::string allChars = "#ABCD0123456789";
  std::string justNums = "0123456789";
  std::string justLetters = "#ABCD";
  if (choose)
  {
    if (id(key) == "D")
    {
      choose = false;
      if (arm_launch)
      {
        arm_launch = false;
        id(arm_delay) = id(arm_delay_max);
      }
      else
      {
        id(disarm_alarm).execute();
        id(alarm_p).show();
        id(my_interval) = 0;
      }
    }
    else
      arm_launch = true;
    return;
  }
  else
  {
    if (id(key) == "*")
    {
      if (id(api_connected))
        id(thermos_p).show();
      else
      {
        id(message_txt) = "Not*connected!";
        id(msg_p).show();
      }
      id(my_display).update();
    }
    else if (id(key) == "#" && id(password_str) == "")
    {
      id(wifi_p).show();
      id(my_display).update();
      id(my_interval) = 0;
    }
    else if (justNums.find(id(key)) != std::string::npos || (justLetters.find(id(key)) != std::string::npos && id(password_str) != "") || (justLetters.find(id(key)) != std::string::npos && id(options)))
    {
      id(password_str).append(id(key));
      if (id(relay_present) && id(password_str) == (id(relay_pw)))
      {
        id(relay).turn_on();
        id(password_str) = "";
      }
#ifdef HOMEASSISTANT
      else if (id(password_str) == id(password).state)
      {
        id(password_str) = "";
        id(choose_pw).show();
        id(my_display).update();
        choose = true;
        buzzer_on();
      }
#endif
      else if (id(password_str).length() == 6 || justLetters.find(id(key)) != std::string::npos)
      {
        static byte c;
        c++;
        String r;
        if (id(options))
        {
          id(password_str) = id(password_str_old).substr(0, id(password_str_old).length() - 1) + id(key);
          id(password_str_old) = "";
          id(options) = false;
        }
        else
          id(password_str_old) = id(password_str);
        r += "{\"try\":";
        r += String(c);
        r += ",\"code\":\"";
        r += id(password_str).c_str();
        r += "\"}";
        id(codeT).publish_state(r.c_str());
        id(checking_pw).show();
        id(my_display).update();
        id(password_str) = "";
        id(my_interval) = 0;
      }
      else
      {
        id(key) = id(key);
        id(key_p).show();
        id(my_display).update();
        id(my_interval) = 2;
      }
    }
    else
    {
      id(password_str) = "";
      static byte c;
      c++;
      String r;
      r += "{\"try\":";
      r += String(c);
      r += ",\"key\":\"";
      r += id(key).c_str();
      r += "\"}";
      id(output_key).publish_state(r.c_str());
    }
  }
}

void alarm_LED()
{
#ifdef HOMEASSISTANT
  static bool led_s;
  led_s = !led_s;
  if (id(cover).state != "closed" && led_s)
    id(led_id).turn_on();
  else
    id(led_id).turn_off();
#endif
}

void screen_roll()
{
  // turn off choose/options screen
  turn_off_choose();
  // arm alarm after delay
  arm_alarm();
  if (WiFi.isConnected())
    if (id(my_interval) >= 4 && !choose && !id(options) && !arm_launch)
    {
      id(my_interval) = 0;
      static auto p = 0;
      p++;
      switch (p)
      {
      case 1:
        id(time_p).show();
#ifndef HOMEASSISTANT
        p = 0;
#endif
        break;
#ifdef HOMEASSISTANT
      case 2:
        id(temp_p).show();
        break;
      case 3:
        // next line avoids further screens to show if device is outdoors
        if ("$location" == "out") // TODO
          p = 0;
        id(garage_p).show();
        break;
      case 4:
        p = 0;
        id(alarm_p).show();
        break;
#endif
      }
    }
    else
      id(my_interval) += 1;
  else
  {
    id(connecting).show();
    id(my_display).update();
  }
}

void keypadEvent(KeypadEvent myKey)
{
  std::string justNums = "0123456789";
  ESP_LOGI("keypadEvent", "looping start!");
  unsigned long p = millis();
  unsigned long m = p;
  while (m - p < 2000)
  {
    m = millis();
    static char myKeyp = NO_KEY;
    static KeyState myKSp = IDLE;
    static auto myHold = false;

    KeyState myKS = myKeypad.getState();
    if (myKSp != myKS && myKS != IDLE)
    {
      myKSp = myKS;
      if (myKey != NULL)
        myKeyp = myKey;
      std::string r;
      r = myKeyp;
      bool isNum = justNums.find(r) != -1;
      ESP_LOGI("keypadEvent", "Key: %s, myKS: %s, isNum: %s", r.c_str(), swOnState(myKS).c_str(), isNum ? "true" : "false");

      if (myKS == HOLD)
        myHold = true;
      if (myKS == PRESSED)
        buzzer_on();
      if (myKS == RELEASED)
      {
        if (myHold)
        {
          r.append("+");
          buzzer_on();
        }
        id(key) = r;
        text_sensor_key_plus();
        if (!isNum || myHold)
        {
          myHold = false;
          ESP_LOGI("keypadEvent", "not a num or hold! break");
          break;
        }
        else
          p = m;
        myHold = false;
      }
      myKey == NULL;
      myKS = IDLE;
    }
    myKey = myKeypad.getKey();
  }
  ESP_LOGI("keypadEvent", "done loop %ds!", m - p);
}

boolean done = false;

void my_loop()
{
  char myKey = myKeypad.getKey();
  if (myKey)
    keypadEvent(myKey);
}

void my_boot()
{
  Wire.begin();
  myKeypad.begin(makeKeymap(keys));
  buzzer_on();
  // myKeypad.addEventListener(keypadEvent); // Add an event listener.
}

byte c = 0;

void not_connected_yet()
{
  // whatever you want to do while no connected
}

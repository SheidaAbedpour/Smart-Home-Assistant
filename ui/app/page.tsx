"use client"

import type React from "react"

// ADD THIS NEW CODE:
async function sendToAssistant(command) {
  try {
    const response = await fetch('http://localhost:8000/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: command })
    });
    const data = await response.json();
    return data.response;
  } catch (error) {
    return `❌ Error: ${error.message}`;
  }
}

import { useState, useEffect } from "react"
import { Send, Globe, Power, Lightbulb, Snowflake, Tv, Clock, Cloud, Newspaper, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

interface Device {
  id: string
  name: string
  nameEn: string
  nameFa: string
  icon: React.ReactNode
  isOn: boolean
  details: string
  detailsEn: string
  detailsFa: string
  category: "lamps" | "acs" | "tvs"
}

export default function SmartHomeDashboard() {
  const [language, setLanguage] = useState<"en" | "fa">("en")
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text:
        language === "en"
          ? "Hello! How can I help you control your smart home today?"
          : "سلام! چطور می‌تونم امروز کمکتون کنم تا خونه هوشمندتون رو کنترل کنید؟",
      isUser: false,
      timestamp: new Date(),
    },
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [currentTime, setCurrentTime] = useState(new Date())

  const [devices, setDevices] = useState<Device[]>([
    {
      id: "1",
      name: "Kitchen Light",
      nameEn: "Kitchen Light",
      nameFa: "چراغ آشپزخانه",
      icon: <Lightbulb className="w-6 h-6" />,
      isOn: true,
      details: "Brightness: 80%",
      detailsEn: "Brightness: 80%",
      detailsFa: "روشنایی: ۸۰٪",
      category: "lamps",
    },
    {
      id: "2",
      name: "Bathroom Light",
      nameEn: "Bathroom Light",
      nameFa: "چراغ حمام",
      icon: <Lightbulb className="w-6 h-6" />,
      isOn: false,
      details: "Off",
      detailsEn: "Off",
      detailsFa: "خاموش",
      category: "lamps",
    },
    {
      id: "3",
      name: "Room 1 Light",
      nameEn: "Room 1 Light",
      nameFa: "چراغ اتاق ۱",
      icon: <Lightbulb className="w-6 h-6" />,
      isOn: true,
      details: "Brightness: 60%",
      detailsEn: "Brightness: 60%",
      detailsFa: "روشنایی: ۶۰٪",
      category: "lamps",
    },
    {
      id: "4",
      name: "Room 2 Light",
      nameEn: "Room 2 Light",
      nameFa: "چراغ اتاق ۲",
      icon: <Lightbulb className="w-6 h-6" />,
      isOn: false,
      details: "Off",
      detailsEn: "Off",
      detailsFa: "خاموش",
      category: "lamps",
    },
    {
      id: "5",
      name: "Room 1 AC",
      nameEn: "Room 1 AC",
      nameFa: "کولر اتاق ۱",
      icon: <Snowflake className="w-6 h-6" />,
      isOn: true,
      details: "Temp: 22°C",
      detailsEn: "Temp: 22°C",
      detailsFa: "دما: ۲۲°س",
      category: "acs",
    },
    {
      id: "6",
      name: "Kitchen AC",
      nameEn: "Kitchen AC",
      nameFa: "کولر آشپزخانه",
      icon: <Snowflake className="w-6 h-6" />,
      isOn: false,
      details: "Off",
      detailsEn: "Off",
      detailsFa: "خاموش",
      category: "acs",
    },
    {
      id: "7",
      name: "Living Room TV",
      nameEn: "Living Room TV",
      nameFa: "تلویزیون پذیرایی",
      icon: <Tv className="w-6 h-6" />,
      isOn: true,
      details: "Channel: Netflix",
      detailsEn: "Channel: Netflix",
      detailsFa: "کانال: نتفلیکس",
      category: "tvs",
    },
  ])

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    setMessages([
      {
        id: "1",
        text:
          language === "en"
            ? "Hello! How can I help you control your smart home today?"
            : "سلام! چطور می‌تونم امروز کمکتون کنم تا خونه هوشمندتون رو کنترل کنید؟",
        isUser: false,
        timestamp: new Date(),
      },
    ])
  }, [language])

  const toggleDevice = (deviceId: string) => {
    setDevices((prev) =>
      prev.map((device) => {
        if (device.id === deviceId) {
          const newIsOn = !device.isOn
          return {
            ...device,
            isOn: newIsOn,
            details: newIsOn
              ? device.category === "lamps"
                ? language === "en"
                  ? "Brightness: 80%"
                  : "روشنایی: ۸۰٪"
                : device.category === "acs"
                  ? language === "en"
                    ? "Temp: 22°C"
                    : "دما: ۲۲°س"
                  : language === "en"
                    ? "Channel: Netflix"
                    : "کانال: نتفلیکس"
              : language === "en"
                ? "Off"
                : "خاموش",
            detailsEn: newIsOn
              ? device.category === "lamps"
                ? "Brightness: 80%"
                : device.category === "acs"
                  ? "Temp: 22°C"
                  : "Channel: Netflix"
              : "Off",
            detailsFa: newIsOn
              ? device.category === "lamps"
                ? "روشنایی: ۸۰٪"
                : device.category === "acs"
                  ? "دما: ۲۲°س"
                  : "کانال: نتفلیکس"
              : "خاموش",
          }
        }
        return device
      }),
    )
  }

  const sendMessage = async () => {
  if (!inputMessage.trim()) return

  const newMessage: Message = {
    id: Date.now().toString(),
    text: inputMessage,
    isUser: true,
    timestamp: new Date(),
  }

  setMessages((prev) => [...prev, newMessage])

  // Get REAL response from Python
  const response = await sendToAssistant(inputMessage);

  const aiResponse: Message = {
    id: (Date.now() + 1).toString(),
    text: response,
    isUser: false,
    timestamp: new Date(),
  }

  setMessages((prev) => [...prev, aiResponse])
  setInputMessage("")
}

  const totalDevices = devices.length
  const activeDevices = devices.filter((d) => d.isOn).length

  const deviceCategories = {
    lamps: { icon: "💡", nameEn: "Lamps", nameFa: "چراغ‌ها" },
    acs: { icon: "❄️", nameEn: "ACs", nameFa: "کولرها" },
    tvs: { icon: "📺", nameEn: "TVs", nameFa: "تلویزیون‌ها" },
  }

  return (
    <div
      className={`min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 text-white ${language === "fa" ? "rtl" : "ltr"}`}
    >
      {/* Header */}
      <header className="backdrop-blur-md border-b border-white/20 p-6 bg-transparent">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">🏠 Smart Home Assistant</h1>
          <p className="text-blue-200 text-lg">
            {language === "en" ? "Multilingual AI-Powered Home Control" : "کنترل خانه هوشمند با هوش مصنوعی چندزبانه"}
          </p>
        </div>
      </header>

      {/* Status Bar */}
      <div className="backdrop-blur-md border-b border-white/10 p-4 bg-indigo-950">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-300">{totalDevices}</div>
            <div className="text-sm text-blue-200">{language === "en" ? "Total Devices" : "کل دستگاه‌ها"}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-300">{activeDevices}</div>
            <div className="text-sm text-blue-200">{language === "en" ? "Active Devices" : "دستگاه‌های فعال"}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-300">✓</div>
            <div className="text-sm text-blue-200">
              {language === "en" ? "Multilingual Support" : "پشتیبانی چندزبانه"}
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-300">🎤</div>
            <div className="text-sm text-blue-200">{language === "en" ? "Voice Ready" : "آماده صوتی"}</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chat Section */}
        <div className="space-y-4">
          <Card className="backdrop-blur-md bg-white/10 border-white/20 h-96">
            <CardContent className="p-4 h-full flex flex-col bg-slate-50">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">{language === "en" ? "AI Assistant" : "دستیار هوش مصنوعی"}</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setLanguage((prev) => (prev === "en" ? "fa" : "en"))}
                  className="border-white/20 hover:bg-white/20 bg-slate-300"
                >
                  <Globe className="w-4 h-4 mr-2" />
                  {language === "en" ? "فارسی" : "English"}
                </Button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 mb-4 bg-slate-100">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isUser ? (language === "fa" ? "justify-start" : "justify-end") : language === "fa" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-xs px-4 py-2 rounded-lg ${
                        message.isUser ? "bg-blue-600 text-white" : "bg-white/20 backdrop-blur-sm"
                      }`}
                    >
                      <p className="text-sm">{message.text}</p>
                      <p className="text-xs opacity-70 mt-1">{message.timestamp.toLocaleTimeString()}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={language === "en" ? "Type your message..." : "پیام خود را تایپ کنید..."}
                  className="border-white/20 text-white placeholder:text-white/60 bg-cyan-600"
                  onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                />
                <Button onClick={sendMessage} className="hover:bg-blue-700 bg-cyan-600">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Device Control */}
        <div className="space-y-4">
          <Card className="backdrop-blur-md bg-white/10 border-white/20">
            <CardContent className="p-4 bg-slate-300">
              <h2 className="text-xl font-semibold mb-4">{language === "en" ? "Device Control" : "کنترل دستگاه‌ها"}</h2>

              {Object.entries(deviceCategories).map(([category, categoryInfo]) => (
                <div key={category} className="mb-6">
                  <h3 className="text-lg font-medium mb-3 flex items-center gap-2">
                    <span>{categoryInfo.icon}</span>
                    {language === "en" ? categoryInfo.nameEn : categoryInfo.nameFa}
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {devices
                      .filter((device) => device.category === category)
                      .map((device) => (
                        <Card
                          key={device.id}
                          className={`cursor-pointer transition-all duration-300 hover:scale-105 ${
                            device.isOn
                              ? "bg-gradient-to-r from-green-500/20 to-blue-500/20 border-green-400/50"
                              : "bg-white/10 border-white/20"
                          } backdrop-blur-sm`}
                          onClick={() => toggleDevice(device.id)}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {device.icon}
                                <span className="font-medium">{language === "en" ? device.nameEn : device.nameFa}</span>
                              </div>
                              <div className={`w-3 h-3 rounded-full ${device.isOn ? "bg-green-400" : "bg-gray-400"}`} />
                            </div>
                            <p className="text-sm text-white/70">
                              {language === "en" ? device.detailsEn : device.detailsFa}
                            </p>
                            <div className="mt-2 flex items-center gap-2">
                              <Power className="w-4 h-4" />
                              <span className="text-sm">
                                {device.isOn
                                  ? language === "en"
                                    ? "ON"
                                    : "روشن"
                                  : language === "en"
                                    ? "OFF"
                                    : "خاموش"}
                              </span>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="max-w-7xl mx-auto p-6">
        <Card className="backdrop-blur-md bg-white/10 border-white/20">
          <CardContent className="p-4 bg-slate-300">
            <h2 className="text-xl font-semibold mb-4">{language === "en" ? "Quick Actions" : "اقدامات سریع"}</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button variant="outline" className="bg-white/10 border-white/20 hover:bg-white/20 h-20 flex-col gap-2">
                <Clock className="w-6 h-6" />
                <div className="text-center">
                  <div className="text-sm font-medium">🕒 {language === "en" ? "Current Time" : "زمان فعلی"}</div>
                  <div className="text-xs">{currentTime.toLocaleTimeString()}</div>
                </div>
              </Button>

              <Button variant="outline" className="bg-white/10 border-white/20 hover:bg-white/20 h-20 flex-col gap-2">
                <Cloud className="w-6 h-6" />
                <div className="text-center">
                  <div className="text-sm font-medium">🌤️ {language === "en" ? "Weather" : "آب و هوا"}</div>
                  <div className="text-xs">{language === "en" ? "22°C Sunny" : "۲۲°س آفتابی"}</div>
                </div>
              </Button>

              <Button variant="outline" className="bg-white/10 border-white/20 hover:bg-white/20 h-20 flex-col gap-2">
                <Newspaper className="w-6 h-6" />
                <div className="text-center">
                  <div className="text-sm font-medium">📰 {language === "en" ? "Latest News" : "آخرین اخبار"}</div>
                  <div className="text-xs">{language === "en" ? "Tech Updates" : "اخبار تکنولوژی"}</div>
                </div>
              </Button>

              <Button variant="outline" className="bg-white/10 border-white/20 hover:bg-white/20 h-20 flex-col gap-2">
                <BarChart3 className="w-6 h-6" />
                <div className="text-center">
                  <div className="text-sm font-medium">📊 {language === "en" ? "Device Status" : "وضعیت دستگاه‌ها"}</div>
                  <div className="text-xs">
                    {activeDevices}/{totalDevices} {language === "en" ? "Active" : "فعال"}
                  </div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

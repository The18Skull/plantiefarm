package com.example.plantfarm

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import com.github.kittinunf.fuel.httpGet
import java.net.URLEncoder
import com.github.kittinunf.fuel.android.extension.responseJson
import com.github.kittinunf.fuel.httpPost

class MainActivity: AppCompatActivity() {
	lateinit var inputMac: TextView
	lateinit var inputText: TextView
	lateinit var outputText: TextView

	override fun onCreate(savedInstanceState: Bundle?) {
		super.onCreate(savedInstanceState)
		setContentView(R.layout.activity_main)

		inputMac = findViewById(R.id.mac)
		inputText = findViewById(R.id.input)
		outputText = findViewById(R.id.output)

		val but0: Button = findViewById(R.id.button_add_dev)
		val but1: Button = findViewById(R.id.button_scan)
		val but2: Button = findViewById(R.id.button_remove)
		val but3: Button = findViewById(R.id.button_get)
		val but4: Button = findViewById(R.id.button_water)
		val but5: Button = findViewById(R.id.button_refresh)

		but0.setOnClickListener { addDevice() }
		but1.setOnClickListener { getDevices() }
		but2.setOnClickListener { simpleGet("remove") }
		but3.setOnClickListener { getSensors() }
		but4.setOnClickListener { simpleGet("water") }
		but5.setOnClickListener { simpleGet("refresh") }
	}

	private fun simpleGet(sub: String) {
		val ip = inputText.text.toString()
		val url = "http://" + ip + ":5000/api/device/" + sub + "?id=0"

		url.httpGet().responseJson { _, _, result ->
			val obj = result.get().obj().getString("msg")
			outputText.text = obj.toString()
		}
	}

	private fun addDevice() {
		val mac = inputMac.text.toString()
		val ip = inputText.text.toString()
		val url = "http://" + ip + ":5000/api/device/add?mac=" + URLEncoder.encode(mac, "UTF-8")

		url.httpPost().responseJson { _, _, result ->
			val obj = result.get().obj().getString("msg")
			outputText.text = obj.toString()
		}
	}

	private fun getDevices() {
		val ip = inputText.text.toString()
		val url = "http://" + ip + ":5000/api/scan"

		url.httpGet().responseJson { _, _, result ->
			val obj = result.get().obj().getString("msg")
			outputText.text = obj.toString()
		}
	}

	private fun getSensors() {
		val ip = inputText.text.toString()
		val url = "http://" + ip + ":5000/api/device/get?id=0"

		url.httpGet().responseJson { _, _, result ->
			val obj = result.get().obj().getJSONObject("msg")
			outputText.text = "Light: ${obj.getDouble("light")}\nWater: ${obj.getDouble("water")}\nTemperature: ${obj.getDouble("temp")}\nHumidity: ${obj.getDouble("hum")}"
		}
	}

}

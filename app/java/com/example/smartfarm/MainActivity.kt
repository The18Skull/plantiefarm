package com.example.smartfarm

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.github.kittinunf.fuel.android.extension.responseJson
import com.github.kittinunf.fuel.httpGet
import com.github.kittinunf.fuel.httpPost
import com.github.mikephil.charting.data.BarData
import com.github.mikephil.charting.data.BarDataSet
import com.github.mikephil.charting.data.BarEntry
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.android.synthetic.main.activity_main.*
import java.io.IOException
import java.net.URLEncoder
import java.util.ArrayList

@ExperimentalStdlibApi
class MainActivity:AppCompatActivity() {
	private var mac: String = "0"
	private var pin: String = "0"
	private var ip: String = "127.0.0.1"
	private var currentDevice: String = "None"

	override fun onCreate(savedInstanceState: Bundle?) {
		super.onCreate(savedInstanceState)
		setContentView(R.layout.activity_main)

		button_add_device.setOnClickListener { button_add_device_routine() }
		button_choose_device.setOnClickListener { button_choose_device_routine() }
		button_remove_device.setOnClickListener { button_remove_device_routine() }
		button_get_measurements.setOnClickListener { button_get_measurements_routine() }
		button_do_watering.setOnClickListener { button_water_routine() }

		text_ip.setOnClickListener { get_ip_routine() }
		layout_humidity.setOnClickListener { label_choose_graph(1) }
		layout_light.setOnClickListener { label_choose_graph(2) }
		layout_temperature.setOnClickListener { label_choose_graph(3) }
		layout_water.setOnClickListener { label_choose_graph(4) }
		val intent = Intent(this, SelectActivity::class.java)
		intent.putExtra("key", 1)
		startActivityForResult(intent, 1)
	}

	override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
		super.onActivityResult(requestCode, resultCode, data)

		if (resultCode == Activity.RESULT_OK) {
			when (requestCode) {
				1    -> {
					this.mac = data?.getStringExtra("address") ?: "0"
					Log.i("rpi", "${this.mac}")
				}
				2    -> {
					val ssid: String = data?.getStringExtra("name") ?: "None"
					Log.i("wifi", "$ssid")
					val inflater = LayoutInflater.from(this).inflate(R.layout.dialog_input, null)
					val editText: EditText = inflater.findViewById(R.id.input_text)
					val builder = AlertDialog.Builder(this)
					builder.setTitle("Введите пароль для подключения к WiFi сети")
					builder.setPositiveButton("Подключиться") { dialog, _ ->
						val pass = editText.text.toString()
						val dev = Device(this.mac, pin)
						dev.connect()

						dev.send("connect $ssid:$pass")
						dev.recv()
						dev.send("check")
						val ret = dev.recv()
						dev.close()
						if (ret != null) {
							this.ip = ret
						}

						dialog.dismiss()
					}
					builder.setNegativeButton("Отмена") { dialog, _ ->
						Log.i("connection", "Connection was aborted")
						dialog.dismiss()
						this.finish()
					}
					builder.setView(inflater)
					val dialog = builder.create()
					dialog.show()
				}
				3    -> {
					val dev = data?.getStringExtra("address")

					if (dev != null) {
						val inflater = LayoutInflater.from(this).inflate(R.layout.dialog_input, null)
						val editText: EditText = inflater.findViewById(R.id.input_text)
						editText.setText("0000")
						val builder = AlertDialog.Builder(this)
						builder.setTitle("Введите PIN-код для подключения")
						builder.setPositiveButton("Подключиться") { dialog, _ ->
							val pin = editText.text.toString()

							try {
								val url = "http://${this.ip}:5000/api/device/add?mac="+URLEncoder.encode(dev, "UTF-8")+"&pin="+URLEncoder.encode(pin, "UTF-8")
								url.httpPost().responseJson { _, _, res ->
									val status = res.get().obj().getBoolean("status")
									val msg = res.get().obj().getString("msg")
									if (status) {
										Toast.makeText(this, "Setup event was added", Toast.LENGTH_SHORT).show()
									} else {
										Toast.makeText(this, "$msg", Toast.LENGTH_SHORT).show()
									}
								}
							} catch (e: IOException) {
								e.printStackTrace()
							}

							dialog.dismiss()
						}
						builder.setNegativeButton("Отмена") { dialog, _ ->
							Log.i("connection", "Connection was aborted")
							dialog.dismiss()
							this.finish()
						}
						builder.setView(inflater)
						val dialog = builder.create()
						dialog.show()
					}
				}
				4    -> {
					this.currentDevice = data?.getStringExtra("address") ?: "None"
					text_current_device.text = "Device: ${this.currentDevice}"
					Log.i("device", "${this.currentDevice}")
				}
				else -> {
					Log.i("activity", "$requestCode is finished")
				}
			}
		}
	}

	private fun get_ip_routine() {
		val inflater = LayoutInflater.from(this).inflate(R.layout.dialog_input, null)
		val editText: EditText = inflater.findViewById(R.id.input_text)
		val builder = AlertDialog.Builder(this)
		builder.setTitle("Введите PIN-код для подключения")
		builder.setPositiveButton("Подключиться") { dialog, _ ->
			if (this.pin == "0") {
				this.pin = editText.text.toString()
			}
			val dev = Device(this.mac, this.pin)
			dev.connect()
			dev.send("check")
			val ret = dev.recv()
			dev.close()
			if (ret != null && !ret.contains("null")) {
				this.ip = ret.toString()
				text_ip.text = "IP: ${this.ip}"
			} else {
				val intent = Intent(this, SelectActivity::class.java)
				intent.putExtra("key", 2)
				intent.putExtra("mac", mac)
				intent.putExtra("pin", pin)
				startActivityForResult(intent, 2)
			}

			dialog.dismiss()
		}
		builder.setNegativeButton("Отмена") { dialog, _ ->
			Log.i("connection", "Connection was aborted")
			dialog.dismiss()
			this.finish()
		}
		builder.setView(inflater)
		val dialog = builder.create()
		dialog.show()
	}

	private fun button_add_device_routine() {
		val intent = Intent(this, SelectActivity::class.java)
		intent.putExtra("key", 3)
		intent.putExtra("ip", this.ip)
		startActivityForResult(intent, 3)
	}

	private fun button_choose_device_routine() {
		val intent = Intent(this, SelectActivity::class.java)
		intent.putExtra("key", 4)
		intent.putExtra("ip", this.ip)
		startActivityForResult(intent, 4)
	}

	private fun button_remove_device_routine() {
		if (this.currentDevice == "None") {
			Toast.makeText(this, "First choose the device", Toast.LENGTH_SHORT).show()
			return
		}

		try {
			val url = "http://${this.ip}:5000/api/device/remove?id="+URLEncoder.encode(this.currentDevice, "UTF-8")
			url.httpPost().responseJson { _, _, res ->
				val status = res.get().obj().getBoolean("status")
				val msg = res.get().obj().getString("msg")
				if (status) {
					Toast.makeText(this, "Device was removed", Toast.LENGTH_SHORT).show()
				} else {
					Toast.makeText(this, "$msg", Toast.LENGTH_SHORT).show()
				}
			}
		} catch (e: IOException) {
			e.printStackTrace()
		}
	}

	private fun button_get_measurements_routine() {
		if (this.currentDevice == "None") {
			Toast.makeText(this, "First choose the device", Toast.LENGTH_SHORT).show()
			return
		}

		try {
			val url = "http://${this.ip}:5000/api/device/last?id="+URLEncoder.encode(this.currentDevice, "UTF-8")
			url.httpGet().responseJson { _, _, res ->
				val status = res.get().obj().getBoolean("status")
				val msg = res.get().obj().getString("msg")

				if (status) {
					Toast.makeText(this, "Got data $msg", Toast.LENGTH_SHORT).show()
					val mapType = object:TypeToken<Map<String, Float>>() {}.type
					val data: Map<String, Float> = Gson().fromJson(msg, mapType)
					for ((k, v) in data) {
						when (k) {
							"hum"   -> text_humidity.text = v.toString()
							"light" -> text_light.text = v.toString()
							"temp"  -> text_temperature.text = v.toString()
							"water" -> text_water.text = v.toString()
							else    -> Toast.makeText(this, "Unknown key $k", Toast.LENGTH_SHORT).show()
						}
					}
				} else {
					Toast.makeText(this, "$msg", Toast.LENGTH_SHORT).show()
					if (msg == "The history is empty. Refresh the device") {
						val url = "http://${this.ip}:5000/api/device/refresh?id="+URLEncoder.encode(this.currentDevice, "UTF-8")
						url.httpGet().responseString { _, _, result ->
							print(result.toString())
						}
					}
				}
			}
		} catch (e: IOException) {
			e.printStackTrace()
		}
	}

	private fun button_water_routine() {
		if (this.currentDevice == "None") {
			Toast.makeText(this, "First choose the device", Toast.LENGTH_SHORT).show()
			return
		}

		try {
			val url = "http://${this.ip}:5000/api/device/water?id="+URLEncoder.encode(this.currentDevice, "UTF-8")
			url.httpPost().responseJson { _, _, res ->
				val status = res.get().obj().getBoolean("status")
				val msg = res.get().obj().getString("msg")
				if (status) {
					Toast.makeText(this, "Water event was added", Toast.LENGTH_SHORT).show()
				} else {
					Toast.makeText(this, "$msg", Toast.LENGTH_SHORT).show()
				}
			}
		} catch (e: IOException) {
			e.printStackTrace()
		}
	}

	private fun label_choose_graph(key: Int) {
		if (this.currentDevice == "None") {
			Toast.makeText(this, "First choose the device", Toast.LENGTH_SHORT).show()
			return
		}

		barchart.clear()
		try {
			val url = "http://${this.ip}:5000/api/device/get?id="+URLEncoder.encode(this.currentDevice, "UTF-8")
			url.httpGet().responseJson { _, _, res ->
				val status = res.get().obj().getBoolean("status")
				val msg = res.get().obj().getString("msg")

				if (status) {
					Log.i("graph", "$msg")
					//Toast.makeText(this, "Got data $msg", Toast.LENGTH_SHORT).show()
				} else {
					Toast.makeText(this, "$msg", Toast.LENGTH_SHORT).show()
					throw IOException("Failed to receive the result")
				}
				val values = ArrayList<BarEntry>()
				val mapType = object:TypeToken<ArrayList<Map<String, Float>>>() {}.type
				val array: ArrayList<Map<String, Float>> = Gson().fromJson(msg, mapType)
				for ((i, item) in array.withIndex()) {
					when (key) {
						1    -> values.add(BarEntry(i.toFloat(), item["hum"] ?: 0.toFloat()))
						2    -> values.add(BarEntry(i.toFloat(), item["light"] ?: 0.toFloat()))
						3    -> values.add(BarEntry(i.toFloat(), item["temp"] ?: 0.toFloat()))
						4    -> values.add(BarEntry(i.toFloat(), item["water"] ?: 0.toFloat()))
						else -> Toast.makeText(this, "Unknown key $key", Toast.LENGTH_SHORT).show()
					}
				}
				val dataset = BarDataSet(values, "Values")
				val data = BarData(dataset)
				barchart.data = data
				barchart.invalidate()
			}
		} catch (e: IOException) {
			e.printStackTrace()
		}
	}
}

package com.example.smartfarm

import android.app.Activity
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.content.Intent
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.widget.AdapterView
import android.widget.SimpleAdapter
import android.widget.Toast
import com.github.kittinunf.fuel.android.extension.responseJson
import java.util.ArrayList
import com.github.kittinunf.fuel.httpGet
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.android.synthetic.main.activity_select.*

@ExperimentalStdlibApi
class SelectActivity:AppCompatActivity() {
	private var btAdapter: BluetoothAdapter? = null
	private val REQUEST_ENABLE_BLUETOOTH = 1

	override fun onCreate(savedInstanceState: Bundle?) {
		super.onCreate(savedInstanceState)
		setContentView(R.layout.activity_select)

		this.btAdapter = BluetoothAdapter.getDefaultAdapter()
		if (this.btAdapter == null) {
			Toast.makeText(this, "The device doesn't support Bluetooth", Toast.LENGTH_SHORT).show()
			return
		}
		if (!this.btAdapter!!.isEnabled) {
			val enableBluetoothIntent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
			startActivityForResult(enableBluetoothIntent, REQUEST_ENABLE_BLUETOOTH)
		}

		button_refresh.setOnClickListener { refreshList() }
		button_refresh.callOnClick()
	}

	private fun refreshList() {
		val key = intent.getIntExtra("key", 0)
		when (key) {
			1    -> refreshPiList()
			2    -> refreshWiFiList()
			3    -> refreshArduinoList()
			4    -> refreshKnownArduinoList()
			else -> 0
		}
	}

	private fun refreshPiList(): Int {
		if (this.btAdapter == null) {
			return 0
		}
		var devices: Set<BluetoothDevice> = this.btAdapter!!.bondedDevices

		if (devices.isNotEmpty()) {
			val list: ArrayList<Map<String, String>> = ArrayList()
			for (dev: BluetoothDevice in devices) {
				val item = mapOf("name" to dev.name, "address" to dev.address)
				list.add(item)
			}
			this.set_items_in_list(list)
		} else {
			Toast.makeText(this, "No Bluetooth devices was found", Toast.LENGTH_SHORT).show()
		}

		return 0
	}

	private fun refreshWiFiList(): Int {
		val mac = intent.getStringExtra("mac") ?: "0"
		val pin = intent.getStringExtra("pin") ?: "0000"
		val dev = Device(mac, pin)
		dev.connect()

		dev.send("scan")
		val raw = dev.recv()
		dev.close()
		if (raw != null) {
			val list: ArrayList<Map<String, String>> = ArrayList()
			val mapType = object :TypeToken<Map<String,String>>() {}.type
			val data: Map<String,String> = Gson().fromJson(raw, mapType)
			for ((k,v) in data) {
				val item = mapOf("name" to v, "address" to k)
				list.add(item)
			}
			this.set_items_in_list(list)
		}

		return 0
	}

	private fun refreshArduinoList(): Int {
		val ip = intent.getStringExtra("ip") ?: "127.0.0.1"

		val url = "http://$ip:5000/api/scan"
		url.httpGet().responseJson { _, _, res ->
			val list: ArrayList<Map<String, String>> = ArrayList()
			val mapType = object :TypeToken<Map<String,String>>() {}.type
			val msg = res.get().obj().getString("msg")
			val data: Map<String,String> = Gson().fromJson(msg, mapType)
			for ((k,v) in data) {
				val item = mapOf("name" to v, "address" to k)
				list.add(item)
			}
			this.set_items_in_list(list)
		}

		return 0
	}

	private fun refreshKnownArduinoList(): Int {
		val ip = intent.getStringExtra("ip") ?: "127.0.0.1"

		val url = "http://$ip:5000/api/devices"
		url.httpGet().responseJson { _, _, res ->
			val list: ArrayList<Map<String, String>> = ArrayList()
			val mapType = object :TypeToken<Map<String,String>>() {}.type
			val msg = res.get().obj().getString("msg")
			val data: Map<String,String> = Gson().fromJson(msg, mapType)
			for ((k,v) in data) {
				val item = mapOf("name" to k, "address" to v)
				list.add(item)
			}
			this.set_items_in_list(list)
		}

		return 0
	}

	private fun set_items_in_list(list: ArrayList<Map<String, String>>) {
		val from: Array<String> = arrayOf("name", "address")
		val to: IntArray = arrayOf(android.R.id.text1, android.R.id.text2).toIntArray()
		val adapter = SimpleAdapter(this, list, android.R.layout.simple_list_item_2, from, to)
		list_items.adapter = adapter
		list_items.onItemClickListener = AdapterView.OnItemClickListener { _, _, pos, _ ->
			val name: String = list[pos]["name"] ?: "None"
			val address: String = list[pos]["address"] ?: "None"

			intent.putExtra("name", name)
			intent.putExtra("address", address)
			setResult(Activity.RESULT_OK, intent)
			finish()
		}
	}

	override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
		super.onActivityResult(requestCode, resultCode, data)
		if (requestCode == REQUEST_ENABLE_BLUETOOTH) {
			if (resultCode == Activity.RESULT_OK) {
				if (this.btAdapter!!.isEnabled) {
					Toast.makeText(this, "Bluetooth has been enabled", Toast.LENGTH_SHORT).show()
				} else {
					Toast.makeText(this, "Bluetooth has been disabled", Toast.LENGTH_SHORT).show()
				}
			} else if (resultCode == Activity.RESULT_CANCELED) {
				Toast.makeText(this, "Bluetooth enabling has been canceled", Toast.LENGTH_SHORT).show()
			}
		}
	}
}

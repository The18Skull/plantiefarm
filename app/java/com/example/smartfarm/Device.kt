package com.example.smartfarm

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothSocket
import android.util.Log
import java.io.IOException
import java.io.InputStream
import java.util.*

@ExperimentalStdlibApi
class Device(address: String, pin: String?) {
	private val uID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
	private val address: String
	private var pin: String = "0000"

	private var btSocket: BluetoothSocket? = null
	private var isConnected: Boolean = false
	private var reader: InputStream? = null

	init {
		this.address = address
		this.pin = pin ?: "0000"
	}

	public fun connect() {
		try {
			if (!this.isConnected) {
				val btAdapter = BluetoothAdapter.getDefaultAdapter()
				val dev = btAdapter.getRemoteDevice(address)
				this.btSocket = dev.createInsecureRfcommSocketToServiceRecord(this.uID)
				btAdapter.cancelDiscovery()

				this.btSocket!!.connect()
				this.reader = this.btSocket!!.inputStream

				this.send(this.pin)
				val res = this.recv()
				if (res == null || !res.contains("OK")) {
					throw IOException("fail")
				}

				this.isConnected = true
				Log.i("connection", "Connected to $address")
			}
		} catch (e: IOException) {
			Log.i("connection", "Failed to connect to $address")
			this.close()
			e.printStackTrace()
		}
	}

	public fun close() {
		if (this.btSocket != null) {
			try {
				this.btSocket!!.close()
				this.reader!!.close()
			} catch (e: NullPointerException) {
				e.printStackTrace()
			}
		}
		this.isConnected = false
		this.btSocket = null
		this.reader = null
	}

	public fun send(msg: String) {
		try {
			this.btSocket!!.outputStream.write("$msg\n".toByteArray())
			Log.i("send", "$msg")
		} catch (e: NullPointerException) {
			Log.i("send", "Failed to send $msg")
			e.printStackTrace()
			this.close()
		}
	}

	public fun recv(): String? {
		try {
			val bytes = ByteArray(1024)
			this.reader!!.read(bytes)

			val res: String = bytes.decodeToString().trim(0.toChar(), 9.toChar(), 10.toChar(), 13.toChar(), 32.toChar())
			Log.i("recv", "$res")

			return res
		} catch (e: NullPointerException) {
			Log.i("recv", "Failed to recv")
			e.printStackTrace()
			this.close()
		}

		return null
	}
}
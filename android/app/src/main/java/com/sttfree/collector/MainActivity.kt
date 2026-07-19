package com.sttfree.collector

import android.Manifest
import android.content.Intent
import android.os.Build
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.sttfree.collector.databinding.ActivityMainBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var settings: SettingsStore

    private val requestPermissions =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        settings = SettingsStore(this)
        requestNeededPermissions()

        binding.buttonSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        binding.buttonSyncNow.setOnClickListener { runSyncNow() }

        if (settings.isConfigured()) {
            SyncScheduler.schedulePeriodic(this)
        }
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
    }

    private fun refreshStatus() {
        binding.textStatus.text = settings.lastSyncSummary
            ?: getString(if (settings.isConfigured()) R.string.status_idle else R.string.status_not_configured)
    }

    private fun runSyncNow() {
        binding.textStatus.text = getString(R.string.status_syncing)
        binding.buttonSyncNow.isEnabled = false
        lifecycleScope.launch {
            withContext(Dispatchers.IO) { SyncManager(this@MainActivity).runSync() }
            binding.buttonSyncNow.isEnabled = true
            refreshStatus()
        }
    }

    private fun requestNeededPermissions() {
        val permissions = mutableListOf<String>()
        permissions += if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.READ_MEDIA_AUDIO
        } else {
            Manifest.permission.READ_EXTERNAL_STORAGE
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions += Manifest.permission.POST_NOTIFICATIONS
        }
        requestPermissions.launch(permissions.toTypedArray())
    }
}

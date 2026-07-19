package com.sttfree.collector

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.sttfree.collector.databinding.ActivitySettingsBinding

class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding
    private lateinit var settings: SettingsStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        title = getString(R.string.settings_title)

        settings = SettingsStore(this)
        binding.editRepoUrl.setText(settings.repoUrl)
        binding.editUsername.setText(settings.username)
        binding.editToken.setText(settings.token)

        binding.buttonSave.setOnClickListener {
            settings.repoUrl = binding.editRepoUrl.text.toString().trim()
            settings.username = binding.editUsername.text.toString().trim()
            settings.token = binding.editToken.text.toString().trim()

            if (settings.isConfigured()) {
                SyncScheduler.schedulePeriodic(this)
            }
            finish()
        }
    }
}

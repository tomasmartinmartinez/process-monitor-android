package com.example.processmonitor.ui

import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.Menu
import android.view.MenuItem
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.processmonitor.R
import com.example.processmonitor.databinding.ActivityMainBinding
import com.example.processmonitor.model.ProcessInfo
import com.example.processmonitor.service.ProcessMonitor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val monitor = ProcessMonitor()
    private val adapter = ProcessAdapter()

    private var fullList: List<ProcessInfo> = emptyList()
    private var filterText: String = ""
    private var sortBy: SortBy = SortBy.CPU
    private var refreshJob: Job? = null

    enum class SortBy { CPU, MEM, NAME, PID }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setSupportActionBar(binding.toolbar)

        binding.recycler.layoutManager = LinearLayoutManager(this)
        binding.recycler.adapter = adapter

        binding.swipe.setOnRefreshListener { updateNow() }

        binding.editSearch.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) {
                filterText = s?.toString()?.trim()?.lowercase() ?: ""
                applyFilterAndSort()
            }
            override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
            override fun onTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
        })

        startRefreshing()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        sortBy = when (item.itemId) {
            R.id.action_sort_cpu -> SortBy.CPU
            R.id.action_sort_mem -> SortBy.MEM
            R.id.action_sort_name -> SortBy.NAME
            R.id.action_sort_pid -> SortBy.PID
            else -> return super.onOptionsItemSelected(item)
        }
        applyFilterAndSort()
        return true
    }

    private fun startRefreshing() {
        refreshJob?.cancel()
        refreshJob = lifecycleScope.launch {
            while (true) {
                updateNow()
                delay(2000)
            }
        }
    }

    private fun updateNow() {
        lifecycleScope.launch {
            val list = withContext(Dispatchers.IO) { monitor.snapshot() }
            fullList = list

            val totalCpu = list.sumOf { it.cpuPercent.toDouble() }.toFloat()
            val totalMem = list.sumOf { it.memKb }
            binding.txtInfo.text = String.format(
                Locale.US,
                "Procesos: %d   |   CPU total: %.1f%%   |   RAM: %s   |   Núcleos: %d",
                list.size, totalCpu, formatMem(totalMem), monitor.numCores
            )

            applyFilterAndSort()
            binding.swipe.isRefreshing = false
        }
    }

    private fun applyFilterAndSort() {
        var filtered = if (filterText.isEmpty()) fullList
                       else fullList.filter {
                           it.name.lowercase().contains(filterText) ||
                           it.pid.toString().contains(filterText) ||
                           it.user.lowercase().contains(filterText)
                       }

        filtered = when (sortBy) {
            SortBy.CPU  -> filtered.sortedByDescending { it.cpuPercent }
            SortBy.MEM  -> filtered.sortedByDescending { it.memKb }
            SortBy.NAME -> filtered.sortedBy { it.name.lowercase() }
            SortBy.PID  -> filtered.sortedBy { it.pid }
        }

        adapter.submitList(filtered)
    }

    private fun formatMem(kb: Long): String = when {
        kb < 1024 -> "${kb} KB"
        kb < 1024 * 1024 -> String.format(Locale.US, "%.1f MB", kb / 1024.0)
        else -> String.format(Locale.US, "%.2f GB", kb / (1024.0 * 1024.0))
    }

    override fun onDestroy() {
        super.onDestroy()
        refreshJob?.cancel()
    }
}

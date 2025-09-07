"""
Main application window with navigation and central layout.
"""

import sys
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStackedWidget, QListWidget, QListWidgetItem, QGroupBox,
    QLabel, QPushButton, QComboBox, QSpinBox, QStatusBar,
    QMenuBar, QToolBar, QApplication, QMessageBox, QFileDialog
)
from PySide6.QtCore import (
    Qt, QTimer, QSettings, Signal, QThread, QSize
)
from PySide6.QtGui import (
    QAction, QIcon, QKeySequence, QCloseEvent, QFont
)

from ..core import DataManager, ConfigManager, BackupManager, ExportManager
from ..models import MonthData, AppSettings
from .widgets import MonthWidget, DashboardWidget, HistoryWidget, ChartsWidget
from .dialogs import SettingsDialog, ExportDialog, AboutDialog


class AutoSaveWorker(QThread):
    """Background thread for auto-save operations."""
    
    save_completed = Signal(bool)
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        
    def run(self):
        """Execute auto-save operation."""
        try:
            success = self.data_manager.save_data()
            self.save_completed.emit(success)
        except Exception:
            self.save_completed.emit(False)


class MainWindow(QMainWindow):
    """
    Main application window with navigation sidebar and content area.
    """
    
    # Signals
    theme_changed = Signal(str)
    data_saved = Signal(bool)
    calculation_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.data_manager = DataManager()
        self.config_manager = ConfigManager()
        self.backup_manager = BackupManager()
        self.export_manager = ExportManager()
        
        # Application state
        self.current_year = datetime.now().year
        self.current_month = self._get_current_month_name()
        self.is_dirty = False
        self.last_save_time = None
        
        # Auto-save
        self.auto_save_timer = QTimer()
        self.auto_save_worker = None
        
        # UI setup
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._apply_settings()
        self._connect_signals()
        
        # Load initial data
        self._load_current_month()
        
        # Start auto-save timer
        self._setup_auto_save()
        
    def _setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("Expense Tracker v2.0")
        self.setMinimumSize(1200, 800)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Navigation panel
        self._setup_navigation_panel()
        
        # Content area
        self._setup_content_area()
        
        # Set splitter proportions
        self.main_splitter.setStretchFactor(0, 0)  # Navigation (fixed)
        self.main_splitter.setStretchFactor(1, 1)  # Content (stretch)
        self.main_splitter.setSizes([280, 920])
    
    def _setup_navigation_panel(self):
        """Setup left navigation panel."""
        nav_widget = QWidget()
        nav_widget.setFixedWidth(280)
        nav_layout = QVBoxLayout(nav_widget)
        
        # Year/Month selector
        selector_group = QGroupBox("Período")
        selector_layout = QVBoxLayout(selector_group)
        
        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Ano:"))
        self.year_selector = QSpinBox()
        self.year_selector.setRange(2020, 2030)
        self.year_selector.setValue(self.current_year)
        self.year_selector.valueChanged.connect(self._on_year_changed)
        year_layout.addWidget(self.year_selector)
        year_layout.addStretch()
        
        # Month selector
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("Mês:"))
        self.month_selector = QComboBox()
        self.month_selector.addItems([
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto", 
            "Setembro", "Outubro", "Novembro", "Dezembro"
        ])
        self.month_selector.setCurrentText(self.current_month)
        self.month_selector.currentTextChanged.connect(self._on_month_changed)
        month_layout.addWidget(self.month_selector)
        
        selector_layout.addLayout(year_layout)
        selector_layout.addLayout(month_layout)
        
        # Navigation list
        nav_group = QGroupBox("Navegação")
        nav_group_layout = QVBoxLayout(nav_group)
        
        self.nav_list = QListWidget()
        self.nav_list.setIconSize(QSize(24, 24))
        
        # Navigation items
        nav_items = [
            ("📊 Dashboard", "dashboard"),
            ("📅 Mês Atual", "month"),
            ("📜 Histórico", "history"), 
            ("📈 Gráficos", "charts"),
            ("📄 Relatórios", "reports")
        ]
        
        for text, data in nav_items:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, data)
            self.nav_list.addItem(item)
        
        self.nav_list.setCurrentRow(1)  # Start with month view
        self.nav_list.currentRowChanged.connect(self._on_navigation_changed)
        
        nav_group_layout.addWidget(self.nav_list)
        
        # Quick summary
        summary_group = QGroupBox("Resumo Rápido")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_labels = {
            'total': QLabel("Total: R$ 0,00"),
            'casa1': QLabel("Casa 1: R$ 0,00"),
            'casa2': QLabel("Casa 2: R$ 0,00"),
            'balance': QLabel("Saldo: R$ 0,00")
        }
        
        for label in self.summary_labels.values():
            label.setWordWrap(True)
            summary_layout.addWidget(label)
        
        # Quick actions
        actions_layout = QVBoxLayout()
        
        self.quick_save_btn = QPushButton("💾 Salvar")
        self.quick_save_btn.clicked.connect(self.save_data)
        
        self.quick_calc_btn = QPushButton("🧮 Calcular")
        self.quick_calc_btn.clicked.connect(self.recalculate)
        
        actions_layout.addWidget(self.quick_save_btn)
        actions_layout.addWidget(self.quick_calc_btn)
        
        # Assemble navigation panel
        nav_layout.addWidget(selector_group)
        nav_layout.addWidget(nav_group)
        nav_layout.addWidget(summary_group)
        nav_layout.addLayout(actions_layout)
        nav_layout.addStretch()
        
        self.main_splitter.addWidget(nav_widget)
    
    def _setup_content_area(self):
        """Setup main content area with stacked widgets."""
        self.content_stack = QStackedWidget()
        
        # Create content widgets
        self.dashboard_widget = DashboardWidget(self.data_manager)
        self.month_widget = MonthWidget(self.data_manager, self.config_manager)
        self.history_widget = HistoryWidget(self.data_manager)
        self.charts_widget = ChartsWidget(self.data_manager)
        
        # Add to stack
        self.content_stack.addWidget(self.dashboard_widget)
        self.content_stack.addWidget(self.month_widget)
        self.content_stack.addWidget(self.history_widget)
        self.content_stack.addWidget(self.charts_widget)
        
        # Reports placeholder
        reports_widget = QWidget()
        reports_layout = QVBoxLayout(reports_widget)
        reports_layout.addWidget(QLabel("📄 Relatórios - Em desenvolvimento"))
        self.content_stack.addWidget(reports_widget)
        
        self.main_splitter.addWidget(self.content_stack)
    
    def _setup_menu_bar(self):
        """Setup application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&Arquivo")
        
        new_action = QAction("&Novo Mês", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_month)
        
        open_action = QAction("&Abrir...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        
        save_action = QAction("&Salvar", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_data)
        
        save_as_action = QAction("Salvar &Como...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as)
        
        file_menu.addAction(new_action)
        file_menu.addSeparator()
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        
        export_action = QAction("&Exportar...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Sair", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Editar")
        
        undo_action = QAction("&Desfazer", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setEnabled(False)
        
        redo_action = QAction("&Refazer", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.setEnabled(False)
        
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        
        settings_action = QAction("&Configurações...", self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("&Visualizar")
        
        dashboard_action = QAction("&Dashboard", self)
        dashboard_action.triggered.connect(lambda: self._switch_to_view(0))
        
        month_action = QAction("&Mês Atual", self)
        month_action.triggered.connect(lambda: self._switch_to_view(1))
        
        history_action = QAction("&Histórico", self)
        history_action.triggered.connect(lambda: self._switch_to_view(2))
        
        charts_action = QAction("&Gráficos", self)
        charts_action.triggered.connect(lambda: self._switch_to_view(3))
        
        view_menu.addAction(dashboard_action)
        view_menu.addAction(month_action)
        view_menu.addAction(history_action)
        view_menu.addAction(charts_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Ferramentas")
        
        backup_action = QAction("&Backup...", self)
        backup_action.triggered.connect(self.create_backup)
        
        restore_action = QAction("&Restaurar...", self)
        restore_action.triggered.connect(self.restore_backup)
        
        tools_menu.addAction(backup_action)
        tools_menu.addAction(restore_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Ajuda")
        
        about_action = QAction("&Sobre...", self)
        about_action.triggered.connect(self.show_about)
        
        help_action = QAction("&Ajuda", self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self.show_help)
        
        help_menu.addAction(help_action)
        help_menu.addSeparator()
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Save action
        save_action = QAction("💾", self)
        save_action.setToolTip("Salvar (Ctrl+S)")
        save_action.triggered.connect(self.save_data)
        toolbar.addAction(save_action)
        
        # Calculate action
        calc_action = QAction("🧮", self)
        calc_action.setToolTip("Recalcular (F5)")
        calc_action.triggered.connect(self.recalculate)
        toolbar.addAction(calc_action)
        
        toolbar.addSeparator()
        
        # Export action
        export_action = QAction("📊", self)
        export_action.setToolTip("Exportar dados")
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)
        
        # Settings action
        settings_action = QAction("⚙️", self)
        settings_action.setToolTip("Configurações")
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
    
    def _setup_status_bar(self):
        """Setup application status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message
        self.status_message = QLabel("Pronto")
        self.status_bar.addWidget(self.status_message)
        
        # Balance indicator
        self.balance_indicator = QLabel("Saldo: R$ 0,00")
        self.status_bar.addPermanentWidget(self.balance_indicator)
        
        # Save status
        self.save_status = QLabel("✓ Salvo")
        self.save_status.setStyleSheet("color: green;")
        self.status_bar.addPermanentWidget(self.save_status)
        
        # Auto-save indicator
        self.auto_save_indicator = QLabel("🔄 Auto-save")
        self.auto_save_indicator.setVisible(False)
        self.status_bar.addPermanentWidget(self.auto_save_indicator)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # F5 for recalculate
        recalc_shortcut = QKeySequence(Qt.Key_F5)
        recalc_action = QAction(self)
        recalc_action.setShortcut(recalc_shortcut)
        recalc_action.triggered.connect(self.recalculate)
        self.addAction(recalc_action)
        
        # Ctrl+1-5 for quick navigation
        for i in range(5):
            shortcut = QKeySequence(f"Ctrl+{i+1}")
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, idx=i: self._switch_to_view(idx))
            self.addAction(action)
    
    def _apply_settings(self):
        """Apply current settings to UI."""
        settings = self.config_manager.get_all()
        
        # Window geometry
        self.resize(settings.get('window_width', 1200), settings.get('window_height', 800))
        if settings.get('window_maximized', False):
            self.showMaximized()
        
        # Font
        font = QFont(settings.get('font_family', 'Segoe UI'), settings.get('font_size', 11))
        QApplication.instance().setFont(font)
    
    def _connect_signals(self):
        """Connect widget signals."""
        # Month widget signals
        self.month_widget.data_changed.connect(self._on_data_changed)
        self.month_widget.calculation_updated.connect(self._on_calculation_updated)
        
        # History widget signals
        self.history_widget.month_selected.connect(self._on_history_month_selected)
        
        # Auto-save timer
        self.auto_save_timer.timeout.connect(self._auto_save)
    
    def _setup_auto_save(self):
        """Setup auto-save functionality."""
        interval = self.config_manager.get('auto_save_interval', 60) * 1000  # Convert to ms
        self.auto_save_timer.start(interval)
    
    def _get_current_month_name(self) -> str:
        """Get current month name in Portuguese."""
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto",
            "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        return months[datetime.now().month - 1]
    
    def _load_current_month(self):
        """Load current month data."""
        self.month_widget.load_month_data(self.current_year, self.current_month)
        self._update_summary()
    
    def _switch_to_view(self, index: int):
        """Switch to specific view by index."""
        self.nav_list.setCurrentRow(index)
        self.content_stack.setCurrentIndex(index)
        
        # Refresh data for specific views
        if index == 0:  # Dashboard
            self.dashboard_widget.refresh_data(self.current_year)
        elif index == 2:  # History
            self.history_widget.refresh_data()
        elif index == 3:  # Charts
            self.charts_widget.refresh_data(self.current_year)
    
    def _on_navigation_changed(self, index: int):
        """Handle navigation selection change."""
        if index >= 0:
            self._switch_to_view(index)
    
    def _on_year_changed(self, year: int):
        """Handle year change."""
        self.current_year = year
        self._load_current_month()
    
    def _on_month_changed(self, month: str):
        """Handle month change."""
        self.current_month = month
        self._load_current_month()
    
    def _on_data_changed(self):
        """Handle data change notification."""
        self.is_dirty = True
        self.save_status.setText("⚠️ Não salvo")
        self.save_status.setStyleSheet("color: orange;")
        
        # Update summary
        self._update_summary()
    
    def _on_calculation_updated(self, results: Dict[str, Any]):
        """Handle calculation update."""
        self._update_summary(results)
        self.calculation_updated.emit(results)
    
    def _on_history_month_selected(self, year: int, month: str):
        """Handle month selection from history."""
        self.year_selector.setValue(year)
        self.month_selector.setCurrentText(month)
        self._switch_to_view(1)  # Switch to month view
    
    def _update_summary(self, results: Optional[Dict[str, Any]] = None):
        """Update quick summary display."""
        if results is None:
            results = self.month_widget.get_current_results()
        
        if results:
            # Update summary labels
            total = results.get('total_expenses', 0)
            casa1 = results.get('casa1_should_pay', 0)
            casa2 = results.get('casa2_should_pay', 0)
            balance = results.get('month_balance', 0)
            
            self.summary_labels['total'].setText(f"Total: R$ {total:,.2f}")
            self.summary_labels['casa1'].setText(f"Casa 1: R$ {casa1:,.2f}")
            self.summary_labels['casa2'].setText(f"Casa 2: R$ {casa2:,.2f}")
            
            # Balance with color coding
            balance_text = f"Saldo: R$ {abs(balance):,.2f}"
            if balance > 0:
                balance_text += " (C2 deve)"
                self.summary_labels['balance'].setStyleSheet("color: #e74c3c;")
            elif balance < 0:
                balance_text += " (C2 crédito)"
                self.summary_labels['balance'].setStyleSheet("color: #27ae60;")
            else:
                self.summary_labels['balance'].setStyleSheet("")
            
            self.summary_labels['balance'].setText(balance_text)
            
            # Update status bar balance
            self.balance_indicator.setText(f"Saldo: R$ {abs(balance):,.2f}")
            if balance > 0:
                self.balance_indicator.setStyleSheet("color: #e74c3c;")
            elif balance < 0:
                self.balance_indicator.setStyleSheet("color: #27ae60;")
            else:
                self.balance_indicator.setStyleSheet("")
    
    def _auto_save(self):
        """Perform auto-save if data is dirty."""
        if self.is_dirty and self.config_manager.get('auto_save', True):
            self.auto_save_indicator.setVisible(True)
            
            # Use background thread for auto-save
            if self.auto_save_worker is None or not self.auto_save_worker.isRunning():
                self.auto_save_worker = AutoSaveWorker(self.data_manager)
                self.auto_save_worker.save_completed.connect(self._on_auto_save_completed)
                self.auto_save_worker.start()
    
    def _on_auto_save_completed(self, success: bool):
        """Handle auto-save completion."""
        self.auto_save_indicator.setVisible(False)
        
        if success:
            self.is_dirty = False
            self.last_save_time = datetime.now()
            self.save_status.setText("✓ Auto-salvo")
            self.save_status.setStyleSheet("color: green;")
            self.status_message.setText("Auto-save concluído")
        else:
            self.status_message.setText("Erro no auto-save")
    
    # Public methods
    def save_data(self) -> bool:
        """Save current data manually."""
        try:
            # Save current month data
            month_data = self.month_widget.get_month_data()
            results = self.month_widget.get_current_results()
            
            success = self.data_manager.save_month_data(
                self.current_year, self.current_month, month_data, results
            )
            
            if success:
                self.is_dirty = False
                self.last_save_time = datetime.now()
                self.save_status.setText("✓ Salvo")
                self.save_status.setStyleSheet("color: green;")
                self.status_message.setText("Dados salvos com sucesso")
                self.data_saved.emit(True)
                return True
            else:
                self.status_message.setText("Erro ao salvar dados")
                self.data_saved.emit(False)
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")
            self.data_saved.emit(False)
            return False
    
    def recalculate(self):
        """Trigger recalculation."""
        self.month_widget.calculate()
        self.status_message.setText("Recálculo concluído")
    
    def new_month(self):
        """Create new month entry."""
        # Implementation for creating new month
        pass
    
    def open_file(self):
        """Open data file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo", "", "JSON Files (*.json)"
        )
        if file_path:
            # Implementation for opening file
            pass
    
    def save_as(self):
        """Save data to specific file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Como", "", "JSON Files (*.json)"
        )
        if file_path:
            # Implementation for save as
            pass
    
    def export_data(self):
        """Open export dialog."""
        dialog = ExportDialog(self.data_manager, self.export_manager, self)
        dialog.exec()
    
    def create_backup(self):
        """Create manual backup."""
        try:
            success, message = self.backup_manager.create_backup(
                Path(self.data_manager.data_file), "manual"
            )
            if success:
                QMessageBox.information(self, "Backup", f"Backup criado: {message}")
            else:
                QMessageBox.warning(self, "Erro", f"Falha no backup: {message}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar backup: {str(e)}")
    
    def restore_backup(self):
        """Restore from backup."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Restaurar Backup", "", "JSON Files (*.json);;Gzip Files (*.gz)"
        )
        if file_path:
            reply = QMessageBox.question(
                self, "Restaurar",
                "Restaurar backup irá substituir os dados atuais. Continuar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    success, message = self.backup_manager.restore_backup(
                        Path(file_path), Path(self.data_manager.data_file)
                    )
                    if success:
                        QMessageBox.information(self, "Sucesso", "Backup restaurado com sucesso")
                        self._load_current_month()
                    else:
                        QMessageBox.warning(self, "Erro", f"Falha na restauração: {message}")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao restaurar: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec() == SettingsDialog.Accepted:
            self._apply_settings()
    
    def show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def show_help(self):
        """Show help documentation."""
        # Implementation for help system
        QMessageBox.information(
            self, "Ajuda", 
            "Documentação disponível em:\nhttps://github.com/expense-tracker/docs"
        )
    
    def closeEvent(self, event: QCloseEvent):
        """Handle application close event."""
        if self.is_dirty:
            reply = QMessageBox.question(
                self, "Dados não salvos",
                "Existem alterações não salvas. Deseja salvar antes de sair?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if self.save_data():
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        # Save window state
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        
        # Stop auto-save timer
        self.auto_save_timer.stop()
        
        # Close managers
        self.data_manager.close()
        self.config_manager.close()
        
        event.accept()

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QDialog, QScrollArea, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, QEvent, QObject
from PySide6.QtGui import QIcon, QDoubleValidator
import configparser
import os
import sys
from controller.database import Database


class EditorEventFilter(QObject):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut:
            self.callback()
            return False
        return super().eventFilter(obj, event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._definir_icone()

        self.config = configparser.ConfigParser()
        self.config.read("config.ini", encoding="utf-8")

        self.db = Database()

        self.setWindowTitle("Ajusta Preço - Carregando...")

        self.produtos = []
        
        self.editor_ativo = None
        self.editor_row = None
        self.editor_column = None

        self._criar_interface()
        
        self._configurar_janela()
        
        fullscreen = self.config.get("Database", "fullscreen", fallback="0")
        
        if fullscreen != "1":
            self._centralizar_janela()
        
        QTimer.singleShot(100, self._carregar_nome_empresa)

    def _definir_icone(self):
        try:
            if getattr(sys, "frozen", False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            icon_path = os.path.join(base_path, "icon", "money-management.ico")

            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")

    def _configurar_janela(self):
        fullscreen = self.config.get("Database", "fullscreen", fallback="0")

        self.setMinimumSize(1000, 600)
        
        if fullscreen == "1":
            self.showMaximized()
        else:
            self.resize(1000, 600)
    
    def _carregar_nome_empresa(self):
        try:
            nome_empresa = self.db.buscar_nome_empresa()
            self.setWindowTitle(f"Ajusta Preço - {nome_empresa}")
        except Exception as e:
            print(f"Aviso: Não foi possível buscar nome da empresa: {e}")
            self.setWindowTitle("Ajusta Preço")

    def _centralizar_janela(self):
        screen_geometry = self.screen().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def _on_radio_custo_total_changed(self, checked):
        if checked:
            self._atualizar_tipo_custo(usar_custo_total=True)

    def _on_radio_custo_repos_changed(self, checked):
        if checked:
            self._atualizar_tipo_custo(usar_custo_total=False)

    def _atualizar_tipo_custo(self, usar_custo_total):
        if not self.produtos:
            return
        
        for i, produto in enumerate(self.produtos):
            produto.usar_custo_total = usar_custo_total
            if produto.preco_venda_novo != produto.preco_venda_min:
                produto.set_preco_venda_novo(produto.preco_venda_novo)
            self._atualizar_linha(i)

    def _criar_interface(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QWidget {
                background-color: white;
                color: black;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f5f5f5;
                color: black;
                gridline-color: #d0d0d0;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: black;
                padding: 5px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
            }
            QLineEdit {
                background-color: white;
                color: black;
                border: 1px solid #c0c0c0;
                padding: 3px;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: black;
                border: 1px solid #c0c0c0;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        frame_top = QFrame()
        frame_top.setStyleSheet("QFrame { background-color: #f0f0f0; }")
        layout_top = QHBoxLayout(frame_top)
        layout_top.setContentsMargins(10, 10, 10, 10)
        
        label_serie = QLabel("Série:")
        label_serie.setStyleSheet("font-weight: bold; font-size: 11pt; background-color: transparent;")
        layout_top.addWidget(label_serie)
        
        self.entry_serie = QLineEdit()
        self.entry_serie.setMaximumWidth(50)
        self.entry_serie.setStyleSheet("font-size: 11pt;")
        self.entry_serie.returnPressed.connect(lambda: self.entry_nota.setFocus())
        layout_top.addWidget(self.entry_serie)
        
        label_nota = QLabel("Nota Fiscal:")
        label_nota.setStyleSheet("font-weight: bold; font-size: 11pt; background-color: transparent;")
        layout_top.addWidget(label_nota)
        
        self.entry_nota = QLineEdit()
        self.entry_nota.setMaximumWidth(100)
        self.entry_nota.setStyleSheet("font-size: 11pt;")
        self.entry_nota.returnPressed.connect(lambda: self.entry_fornecedor.setFocus())
        layout_top.addWidget(self.entry_nota)
        
        btn_buscar_notas = QPushButton("🔍")
        btn_buscar_notas.setMaximumWidth(40)
        btn_buscar_notas.setToolTip("Buscar Notas Fiscais")
        btn_buscar_notas.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border: 2px solid #2196F3;
            }
            QPushButton:pressed {
                background-color: #bbdefb;
                border: 2px solid #1976D2;
            }
        """)
        btn_buscar_notas.clicked.connect(self._abrir_busca_notas)
        layout_top.addWidget(btn_buscar_notas)
        
        label_fornecedor = QLabel("Fornecedor:")
        label_fornecedor.setStyleSheet("font-weight: bold; font-size: 11pt; background-color: transparent;")
        layout_top.addWidget(label_fornecedor)
        
        self.entry_fornecedor = QLineEdit()
        self.entry_fornecedor.setMaximumWidth(100)
        self.entry_fornecedor.setStyleSheet("font-size: 11pt;")
        self.entry_fornecedor.returnPressed.connect(self._on_fornecedor_return)
        self.entry_fornecedor.editingFinished.connect(self._atualizar_nome_fornecedor)
        layout_top.addWidget(self.entry_fornecedor)
        
        self.label_nome_fornecedor = QLabel("")
        self.label_nome_fornecedor.setStyleSheet("font-size: 11pt; background-color: transparent;")
        layout_top.addWidget(self.label_nome_fornecedor)
        
        btn_carregar = QPushButton("Carregar")
        btn_carregar.clicked.connect(self._carregar_produtos)
        layout_top.addWidget(btn_carregar)
        
        layout_top.addStretch()
        
        label_base_calculo = QLabel("Base para cálculo:")
        label_base_calculo.setStyleSheet("font-weight: bold; font-size: 10pt; background-color: transparent;")
        layout_top.addWidget(label_base_calculo)
        
        self.button_group_custo = QButtonGroup()
        
        radio_style = """
            QRadioButton {
                font-size: 10pt;
                spacing: 5px;
                background-color: transparent;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
                border-radius: 9px;
                border: 2px solid #666;
            }
            QRadioButton::indicator:checked {
                background-color: #2196F3;
                border: 2px solid #1976D2;
            }
            QRadioButton::indicator:hover {
                border: 2px solid #2196F3;
            }
        """
        
        self.radio_custo_total = QRadioButton("Custo Na Nota")
        self.radio_custo_total.setStyleSheet(radio_style)
        self.radio_custo_total.toggled.connect(self._on_radio_custo_total_changed)
        self.button_group_custo.addButton(self.radio_custo_total)
        layout_top.addWidget(self.radio_custo_total)
        
        self.radio_custo_repos = QRadioButton("Custo Reposição + ICMS")
        self.radio_custo_repos.setChecked(True)
        self.radio_custo_repos.setStyleSheet(radio_style)
        self.radio_custo_repos.toggled.connect(self._on_radio_custo_repos_changed)
        self.button_group_custo.addButton(self.radio_custo_repos)
        layout_top.addWidget(self.radio_custo_repos)
        
        main_layout.addWidget(frame_top)
        
        self.table = QTableWidget()
        self.table.setColumnCount(10) 
        self.table.setHorizontalHeaderLabels([
            "✏", "Seq", "Código", "Descrição", "Custo Na Nota",
            "Custo Reposição + ICMS", "Preço Venda Anterior",
            "Preço Venda Novo", "Margem (%)", "Porcentagem (%)"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Coluna ícone
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Seq
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Código
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Descrição
        self.table.setColumnWidth(0, 30)   # Coluna do ícone (lápis)
        self.table.setColumnWidth(1, 40)   # Seq reduzida
        self.table.setColumnWidth(2, 80)   # Código
        self.table.setColumnWidth(4, 130)  # Custo Na Nota
        self.table.setColumnWidth(5, 160)  # Custo Reposição + ICMS
        self.table.setColumnWidth(6, 140)  # Preço Venda Anterior
        self.table.setColumnWidth(7, 140)  # Preço Venda Novo
        self.table.setColumnWidth(8, 120)  # Margem (%)
        self.table.setColumnWidth(9, 120)  # Porcentagem (%)
        
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.verticalHeader().setVisible(False)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.cellDoubleClicked.connect(self._editar_celula)
        
        main_layout.addWidget(self.table)
        
        frame_bottom = QFrame()
        frame_bottom.setStyleSheet("QFrame { background-color: #f0f0f0; }")
        frame_bottom.setMinimumHeight(60)
        frame_bottom.setMaximumHeight(60)
        layout_bottom = QHBoxLayout(frame_bottom)
        layout_bottom.setContentsMargins(10, 10, 10, 10)
        
        self.label_status = QLabel("")
        self.label_status.setStyleSheet("color: blue; font-size: 9pt; background-color: transparent;")
        layout_bottom.addWidget(self.label_status)
        
        layout_bottom.addStretch()
        
        self.label_alerta_nota = QLabel("")
        self.label_alerta_nota.setStyleSheet("""
            color: #d32f2f;
            font-size: 9pt;
            font-weight: bold;
            background-color: transparent;
        """)
        self.label_alerta_nota.setVisible(False)
        layout_bottom.addWidget(self.label_alerta_nota)
        
        btn_gravar = QPushButton("Gravar")
        btn_gravar.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 11pt;
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_gravar.clicked.connect(self._gravar_precos)
        layout_bottom.addWidget(btn_gravar)
        
        main_layout.addWidget(frame_bottom)
        
        self.entry_serie.setFocus()
    
    def _on_fornecedor_return(self):
        self._atualizar_nome_fornecedor()
        self._carregar_produtos()

    def _carregar_produtos(self):
        serie_nota = self.entry_serie.text().strip()
        numero_nota = self.entry_nota.text().strip()
        codigo_fornecedor = self.entry_fornecedor.text().strip()

        if not serie_nota:
            QMessageBox.warning(
                self, "Atenção", "Por favor, informe a série da nota fiscal."
            )
            return

        if not numero_nota:
            QMessageBox.warning(
                self, "Atenção", "Por favor, informe o número da nota fiscal."
            )
            return

        if not codigo_fornecedor:
            QMessageBox.warning(
                self, "Atenção", "Por favor, informe o código do fornecedor."
            )
            return

        # Verificar se nota já foi processada
        try:
            from controller.notas_processadas import NotasProcessadasManager
            notas_manager = NotasProcessadasManager()
            
            if notas_manager.verificar_nota(codigo_fornecedor, numero_nota, serie_nota):
                info_nota = notas_manager.obter_informacoes(codigo_fornecedor, numero_nota, serie_nota)
                
                mensagem = (
                    f"⚠ ATENÇÃO: Esta nota já foi processada!\n\n"
                    f"Data: {info_nota.get('data', 'N/A')}\n"
                    f"Hora: {info_nota.get('hora', 'N/A')}\n"
                    f"Produtos alterados: {info_nota.get('produtos_editados', 0)}\n\n"
                    f"Deseja carregar a nota mesmo assim?"
                )
                
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Nota Já Processada")
                msg_box.setText(mensagem)
                msg_box.setIcon(QMessageBox.Icon.Warning)
                
                btn_sim = msg_box.addButton("Sim, Carregar", QMessageBox.ButtonRole.YesRole)
                btn_nao = msg_box.addButton("Não, Cancelar", QMessageBox.ButtonRole.NoRole)
                
                msg_box.exec()
                
                if msg_box.clickedButton() != btn_sim:
                    return
        except Exception as e:
            print(f"Aviso: Erro ao verificar nota processada: {e}")

        try:
            self.table.setRowCount(0)

            self.label_status.setText("Carregando produtos...")
            self.repaint()

            self.produtos = self.db.buscar_produtos_por_nota(
                numero_nota, serie_nota, codigo_fornecedor
            )

            if not self.produtos:
                QMessageBox.information(
                    self,
                    "Informação",
                    f"Nenhum produto encontrado para a nota {numero_nota} série {serie_nota} do fornecedor {codigo_fornecedor}.",
                )
                self.label_status.setText("")
                return

            self.table.setRowCount(len(self.produtos))
            
            for i, produto in enumerate(self.produtos):
                icon_item = QTableWidgetItem("")
                icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 0, icon_item)
                
                self.table.setItem(i, 1, QTableWidgetItem(str(produto.sequencia)))
                self.table.setItem(i, 2, QTableWidgetItem(str(produto.codigo)))
                self.table.setItem(i, 3, QTableWidgetItem(produto.descricao))
                self.table.setItem(i, 4, QTableWidgetItem(f"R$ {produto.custo_total:.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(f"R$ {produto.custo_reposicao:.2f}"))
                self.table.setItem(i, 6, QTableWidgetItem(f"R$ {produto.preco_venda_min:.2f}"))
                self.table.setItem(i, 7, QTableWidgetItem(f"▶ R$ {produto.preco_venda_novo:.2f}"))
                self.table.setItem(i, 8, QTableWidgetItem(f"▶ {produto.margem_venda:.2f}"))
                self.table.setItem(i, 9, QTableWidgetItem(f"▶ {produto.porcentagem_custo:.2f}"))
                
                for col in [0, 1, 2]:
                    self.table.item(i, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                for col in [4, 5, 6, 7, 8, 9]:
                    self.table.item(i, col).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self.label_status.setText(f"{len(self.produtos)} produto(s) carregado(s).")
            
            # Verificar alerta de ICMS apenas para Regime Normal (código 3)
            regime_tributario = self.db.buscar_regime_tributario()
            produtos_com_erro = [p for p in self.produtos if p.ar_pen > 0 and p.ag_pen not in [2, 3]]
            if produtos_com_erro and regime_tributario == 3:
                self.label_alerta_nota.setText("⚠ Nota lançada incorretamente (Campo Aproveita ICMS)")
                self.label_alerta_nota.setVisible(True)
            else:
                self.label_alerta_nota.setVisible(False)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos:\n{str(e)}")
            self.label_status.setText("")
            self.label_alerta_nota.setVisible(False)

    def _editar_celula(self, row, column):
        if column not in [7, 8, 9]:
            return

        if row >= len(self.produtos):
            return

        self._fechar_editor_ativo()

        current_item = self.table.item(row, column)
        if current_item:
            current_value = current_item.text()
            current_value = (
                current_value.replace("R$ ", "").replace("▶ ", "").replace(",", ".")
            )
        else:
            current_value = ""

        editor = QLineEdit(self.table)
        editor.setStyleSheet("""
            QLineEdit {
                background-color: #FFFACD;
                font-weight: bold;
                font-size: 10pt;
                color: black;
            }
        """)
        editor.setAlignment(Qt.AlignmentFlag.AlignRight)
        editor.setText(current_value)
        editor.selectAll()
        
        valor_original = current_value
        
        self.editor_ativo = editor
        self.editor_row = row
        self.editor_column = column
        
        salvou = [False]
        pular_proximo = [False] 
        
        original_key_press = editor.keyPressEvent
        
        def custom_key_press(event):
            if event.key() == Qt.Key.Key_Escape:
                if not salvou[0]:
                    salvou[0] = True
                    self._fechar_editor_ativo()
                return
            
            key = event.key()
            text = event.text()
            
            if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Left, 
                      Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End,
                      Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                original_key_press(event)
                return
            
            if text and text not in "0123456789,.":
                return
            
            current_text = editor.text()
            if text in ",." and ("," in current_text or "." in current_text):
                return
            
            original_key_press(event)
        
        def salvar_edicao_focus_out():
            if not salvou[0]:
                pular_proximo[0] = False
                salvar_edicao()
        
        event_filter = EditorEventFilter(salvar_edicao_focus_out)
        editor.installEventFilter(event_filter)
        editor._event_filter = event_filter
                
        def salvar_edicao():
            if salvou[0]:
                return
            salvou[0] = True
            
            novo_valor = editor.text().strip()
            deve_pular = pular_proximo[0]
            
            self._fechar_editor_ativo()
            
            valor_original_normalizado = valor_original.replace(",", ".").strip()
            novo_valor_normalizado = novo_valor.replace(",", ".").strip()
            
            if novo_valor_normalizado == valor_original_normalizado:
                if deve_pular:
                    self._ir_para_proximo_produto(row, column)
                return
            
            if not novo_valor:
                return
            
            try:
                valor_float = float(novo_valor_normalizado)

                if column == 7:
                    self.produtos[row].set_preco_venda_novo(valor_float)
                    self._atualizar_linha(row)
                    if self._verificar_linha_editada(row):
                        self._marcar_linha_editada(row)
                    else:
                        self._desmarcar_linha_editada(row)
                elif column == 8:
                    self.produtos[row].calcular_preco_por_margem_venda(valor_float)
                    self._atualizar_linha(row)
                    if self._verificar_linha_editada(row):
                        self._marcar_linha_editada(row)
                    else:
                        self._desmarcar_linha_editada(row)
                elif column == 9:
                    self.produtos[row].calcular_preco_por_porcentagem_custo(valor_float)
                    self._atualizar_linha(row)
                    if self._verificar_linha_editada(row):
                        self._marcar_linha_editada(row)
                    else:
                        self._desmarcar_linha_editada(row)
                        self._desmarcar_linha_editada(row)

                if deve_pular:
                    self._ir_para_proximo_produto(row, column)

            except ValueError:
                QMessageBox.warning(
                    self, "Atenção", "Por favor, informe um valor numérico válido."
                )
        
        def salvar_edicao_enter():
            pular_proximo[0] = True
            salvar_edicao()
        
        editor.keyPressEvent = custom_key_press
        
        editor.returnPressed.connect(salvar_edicao_enter)
        
        self.table.setCellWidget(row, column, editor)
        editor.setFocus()

    def _fechar_editor_ativo(self):
        if self.editor_ativo is not None and self.editor_row is not None and self.editor_column is not None:
            self.table.removeCellWidget(self.editor_row, self.editor_column)
            self.editor_ativo = None
            self.editor_row = None
            self.editor_column = None

    def _ir_para_proximo_produto(self, row_atual, column):
        produto_index = row_atual - 1 
        if produto_index + 1 < len(self.produtos):
            next_row = row_atual + 1
            self.table.setCurrentCell(next_row, column)
            QTimer.singleShot(50, lambda: self._editar_celula(next_row, column))

    def _atualizar_linha(self, produto_index):
        produto = self.produtos[produto_index]
        row = produto_index 
        
        item_preco = self.table.item(row, 7)
        item_margem = self.table.item(row, 8)
        item_porcentagem = self.table.item(row, 9)
        
        if item_preco:
            item_preco.setText(f"▶ R$ {produto.preco_venda_novo:.2f}")
        if item_margem:
            item_margem.setText(f"▶ {produto.margem_venda:.2f}")
        if item_porcentagem:
            item_porcentagem.setText(f"▶ {produto.porcentagem_custo:.2f}")

    def _marcar_linha_editada(self, row):
        icon_item = self.table.item(row, 0)
        if icon_item:
            icon_item.setText("✏️")
            icon_item.setBackground(Qt.GlobalColor.yellow)
    
    def _desmarcar_linha_editada(self, row):
        icon_item = self.table.item(row, 0)
        if icon_item:
            icon_item.setText("")
            icon_item.setBackground(Qt.GlobalColor.white)
    
    def _verificar_linha_editada(self, row):
        if row >= len(self.produtos):
            return False
        
        produto = self.produtos[row]
        
        try:
            return abs(float(produto.preco_venda_novo) - float(produto.preco_venda_min)) > 0.001
        except (ValueError, AttributeError):
            return False

    def _atualizar_nome_fornecedor(self):
        codigo_fornecedor = self.entry_fornecedor.text().strip()

        if not codigo_fornecedor:
            self.label_nome_fornecedor.setText("")
            return

        try:
            info_fornecedor = self.db.buscar_informacoes_fornecedor(codigo_fornecedor)

            if info_fornecedor:
                self.label_nome_fornecedor.setText(info_fornecedor["nome"])
            else:
                self.label_nome_fornecedor.setText("")

        except Exception as e:
            self.label_nome_fornecedor.setText("")

    def _gravar_precos(self):
        if not self.produtos:
            QMessageBox.warning(self, "Atenção", "Nenhum produto carregado para gravar.")
            return

        # Verificar se há nota lançada incorretamente (apenas para Regime Normal - código 3)
        # Empresas do Simples Nacional não aproveitam ICMS, então não precisam dessa validação
        regime_tributario = self.db.buscar_regime_tributario()
        produtos_com_erro = [p for p in self.produtos if p.ar_pen > 0 and p.ag_pen not in [2, 3]]
        if produtos_com_erro and regime_tributario == 3:
            QMessageBox.critical(
                self,
                "Erro",
                "Não é possível gravar os preços!\n\n"
                "A nota foi lançada incorretamente (Campo Aproveita ICMS).\n"
                "Por favor, corrija o lançamento da nota antes de prosseguir."
            )
            return

        produtos_editados = []
        for row in range(len(self.produtos)):
            icon_item = self.table.item(row, 0)
            if icon_item and icon_item.text() == "✏️":
                produtos_editados.append(self.produtos[row])
        
        if not produtos_editados:
            QMessageBox.warning(
                self, 
                "Atenção", 
                "Nenhum produto foi editado. Altere os preços antes de gravar."
            )
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar")
        msg_box.setText(f"Deseja gravar os novos preços de {len(produtos_editados)} produto(s) editado(s)?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() != btn_sim:
            return

        try:
            self.label_status.setText("Gravando preços...")
            self.repaint()

            # Obter dados da nota para registrar no JSON
            codigo_fornecedor = self.entry_fornecedor.text().strip()
            numero_nota = self.entry_nota.text().strip()
            serie = self.entry_serie.text().strip() or "1"

            self.db.atualizar_precos(
                produtos_editados,
                codigo_fornecedor=codigo_fornecedor,
                numero_nota=numero_nota,
                serie=serie
            )

            QMessageBox.information(
                self, 
                "Sucesso", 
                f"{len(produtos_editados)} preço(s) atualizado(s) com sucesso!"
            )

            msg_etiquetas = QMessageBox(self)
            msg_etiquetas.setWindowTitle("Gerar Etiquetas")
            msg_etiquetas.setText("Deseja gerar as etiquetas dos produtos alterados?")
            msg_etiquetas.setIcon(QMessageBox.Icon.Question)
            
            btn_sim_etiquetas = msg_etiquetas.addButton("Sim", QMessageBox.ButtonRole.YesRole)
            btn_nao_etiquetas = msg_etiquetas.addButton("Não", QMessageBox.ButtonRole.NoRole)
            
            msg_etiquetas.exec()
            
            if msg_etiquetas.clickedButton() == btn_sim_etiquetas:
                self._processar_geracao_etiquetas(produtos_editados)
            else:
                self._limpar_tela()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gravar preços:\n{str(e)}")
            self.label_status.setText("")

    def _processar_geracao_etiquetas(self, produtos_editados):
        
        dialog = self._criar_modal_confirmacao_etiquetas(produtos_editados)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.label_status.setText("Gerando etiquetas...")
                self.repaint()
                
                from controller.etiqueta_generator import EtiquetaGenerator
                
                gerador = EtiquetaGenerator(self.db)
                pdf_path = gerador.gerar_pdf(produtos_editados)
                
                self.label_status.setText("")
                
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Sucesso")
                msg_box.setText(f"Etiquetas geradas com sucesso!\n\n{len(produtos_editados)} etiqueta(s) criada(s).\n\nDeseja abrir o PDF?")
                msg_box.setIcon(QMessageBox.Icon.Information)
                
                btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
                btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
                
                msg_box.exec()
                
                if msg_box.clickedButton() == btn_sim:
                    os.startfile(pdf_path)
                
                self._limpar_tela()
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar etiquetas:\n{str(e)}")
                self.label_status.setText("")
                self._limpar_tela()
        else:
            self._limpar_tela()

    def _criar_modal_confirmacao_etiquetas(self, produtos):
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirmar Geração de Etiquetas")
        dialog.setMinimumSize(700, 400)
        
        layout = QVBoxLayout()
        
        label_titulo = QLabel(f"<b>Etiquetas serão geradas para {len(produtos)} produto(s):</b>")
        label_titulo.setStyleSheet("font-size: 12pt; padding: 10px;")
        layout.addWidget(label_titulo)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Código", "Descrição", "Preço Novo"])
        table.setRowCount(len(produtos))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        
        for i, produto in enumerate(produtos):
            table.setItem(i, 0, QTableWidgetItem(str(produto.codigo)))
            table.setItem(i, 1, QTableWidgetItem(produto.descricao))
            preco_texto = f"R$ {produto.preco_venda_novo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            table.setItem(i, 2, QTableWidgetItem(preco_texto))
        
        table.setColumnWidth(0, 100)
        table.setColumnWidth(1, 400)
        table.setColumnWidth(2, 120)
        
        table_layout.addWidget(table)
        table_widget.setLayout(table_layout)
        scroll.setWidget(table_widget)
        
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 10pt;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_gerar = QPushButton("Gerar Etiquetas")
        btn_gerar.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: bold;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_gerar.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_gerar)
        
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        return dialog

    def _abrir_busca_notas(self):
        try:
            self.label_status.setText("Carregando notas...")
            self.repaint()
            
            notas = self.db.buscar_todas_notas(limite=500)
            
            self.label_status.setText("")
            
            if not notas:
                QMessageBox.information(
                    self,
                    "Informação",
                    "Nenhuma nota fiscal encontrada no sistema."
                )
                return
            
            dialog = self._criar_modal_busca_notas(notas)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                nota_selecionada = dialog.nota_selecionada
                if nota_selecionada:
                    self.entry_serie.setText(nota_selecionada['serie'])
                    self.entry_nota.setText(nota_selecionada['nota'])
                    self.entry_fornecedor.setText(nota_selecionada['codigo_fornecedor'])
                    self._atualizar_nome_fornecedor()
                    self._carregar_produtos()
        
        except Exception as e:
            self.label_status.setText("")
            QMessageBox.critical(self, "Erro", f"Erro ao buscar notas:\n{str(e)}")

    def _criar_modal_busca_notas(self, notas):
        dialog = QDialog(self)
        dialog.setWindowTitle("Buscar Nota Fiscal de Entrada")
        dialog.setMinimumSize(1000, 600)
        dialog.nota_selecionada = None
        
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filtrar:")
        filter_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        filter_layout.addWidget(filter_label)
        
        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Digite para filtrar por nota, fornecedor, CNPJ...")
        filter_input.setStyleSheet("font-size: 10pt; padding: 5px;")
        filter_layout.addWidget(filter_input)
        
        layout.addLayout(filter_layout)
        
        # Obter ícone nativo de confirmação do Qt
        style = self.style()
        icon_processada = style.standardIcon(style.StandardPixmap.SP_DialogApplyButton)
        
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "✓", "Emissão", "Nota", "Série", "Fornecedor", "CNPJ", 
            "Entrada", "Valor", "Status"
        ])
        table.setRowCount(len(notas))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #BBDEFB;
                color: black;
            }
            QTableWidget::item:hover {
                background-color: #E3F2FD;
            }
        """)
        
        for i, nota in enumerate(notas):
            # Coluna 0: Indicador de processada com ícone Qt nativo
            processada_item = QTableWidgetItem("")
            processada_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if nota.get('processada', False):
                processada_item.setIcon(icon_processada)
            table.setItem(i, 0, processada_item)
            
            emissao_str = nota['emissao'].strftime("%d/%m/%Y") if nota['emissao'] else ""
            table.setItem(i, 1, QTableWidgetItem(emissao_str))
            
            table.setItem(i, 2, QTableWidgetItem(nota['nota']))
            
            table.setItem(i, 3, QTableWidgetItem(nota['serie']))
            
            fornecedor_texto = f"{nota['codigo_fornecedor']} - {nota['fornecedor']}"
            table.setItem(i, 4, QTableWidgetItem(fornecedor_texto))
            
            table.setItem(i, 5, QTableWidgetItem(nota['cnpj']))
            
            entrada_str = nota['entrada'].strftime("%d/%m/%Y") if nota['entrada'] else ""
            table.setItem(i, 6, QTableWidgetItem(entrada_str))
            
            valor_texto = f"R$ {nota['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            table.setItem(i, 7, QTableWidgetItem(valor_texto))
            
            table.setItem(i, 8, QTableWidgetItem(nota['status']))
        
        table.setColumnWidth(0, 40)   # Processada (ícone)
        table.setColumnWidth(1, 90)   # Emissão
        table.setColumnWidth(2, 80)   # Nota
        table.setColumnWidth(3, 60)   # Série
        table.setColumnWidth(4, 300)  # Fornecedor
        table.setColumnWidth(5, 130)  # CNPJ
        table.setColumnWidth(6, 90)   # Entrada
        table.setColumnWidth(7, 100)  # Valor
        table.setColumnWidth(8, 180)  # Status
        
        def filtrar_tabela():
            filtro = filter_input.text().lower()
            for i in range(table.rowCount()):
                mostrar = False
                for j in range(table.columnCount()):
                    item = table.item(i, j)
                    if item and filtro in item.text().lower():
                        mostrar = True
                        break
                table.setRowHidden(i, not mostrar)
        
        filter_input.textChanged.connect(filtrar_tabela)
        
        def ao_duplo_clique(item):
            row = item.row()
            dialog.nota_selecionada = notas[row]
            dialog.accept()
        
        table.itemDoubleClicked.connect(ao_duplo_clique)
        
        layout.addWidget(table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 10pt;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancelar)
        
        btn_selecionar = QPushButton("Selecionar")
        btn_selecionar.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        def selecionar_nota():
            selected_items = table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                dialog.nota_selecionada = notas[row]
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Atenção", "Selecione uma nota fiscal.")
        
        btn_selecionar.clicked.connect(selecionar_nota)
        btn_layout.addWidget(btn_selecionar)
        
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        return dialog

    def _limpar_tela(self):
        self.entry_serie.clear()
        self.entry_nota.clear()
        self.entry_fornecedor.clear()
        self.label_nome_fornecedor.setText("")

        self.table.setRowCount(0)

        self.produtos = []

        self.label_status.setText("")

        self.entry_serie.setFocus()

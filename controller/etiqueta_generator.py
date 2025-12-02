import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import barcode
from barcode.writer import ImageWriter
from io import BytesIO


class EtiquetaGenerator:
    ETIQUETA_WIDTH = 100 * mm
    ETIQUETA_HEIGHT = 25 * mm
    
    def __init__(self, database):
        self.db = database
    
    def _obter_codigo_barras(self, codigo_produto):
        if not self.db.connection:
            self.db.connect()
        
        query = """
            SELECT BO_ITE as CodigoBarras, AU_ITE as CodigoProduto
            FROM CE_PRODUTO
            WHERE AU_ITE = ?
        """
        
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(query, (codigo_produto,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                if row.CodigoBarras and str(row.CodigoBarras).strip():
                    return str(row.CodigoBarras).strip()
                elif row.CodigoProduto:
                    return str(row.CodigoProduto).strip()
            
            return str(codigo_produto).strip()
        except Exception as e:
            print(f"Erro ao buscar código de barras: {e}")
            return str(codigo_produto).strip()
    
    def _gerar_codigo_barras_imagem(self, codigo):
        if not codigo or len(codigo) < 3:
            return None
        
        try:
            if len(codigo) == 13 or len(codigo) == 12:
                ean = barcode.get('ean13', codigo, writer=ImageWriter())
            elif len(codigo) == 8 or len(codigo) == 7:
                ean = barcode.get('ean8', codigo, writer=ImageWriter())
            else:
                ean = barcode.get('code128', codigo, writer=ImageWriter())
            
            buffer = BytesIO()
            ean.write(buffer, options={
                'module_width': 0.35,
                'module_height': 15,
                'quiet_zone': 0.5,
                'font_size': 8,
                'text_distance': 4,
                'write_text': True,
                'dpi': 300,
            })
            buffer.seek(0)
            
            return ImageReader(buffer)
        except Exception as e:
            print(f"Erro ao gerar código de barras para {codigo}: {e}")
            return None
    
    def _desenhar_etiqueta(self, c, produto, y_position, codigo_barras_ean):
        margin_left = -3 * mm
        margin_top = y_position
        
        c.setFont("Helvetica-Bold", 14)
        descricao = produto.descricao[:60]
        
        desc_width = c.stringWidth(descricao, "Helvetica-Bold", 14)
        x_desc = margin_left + (self.ETIQUETA_WIDTH - desc_width) / 2
        c.drawString(x_desc, margin_top + 20*mm, descricao)
        
        if codigo_barras_ean:
            barcode_img = self._gerar_codigo_barras_imagem(codigo_barras_ean)
            if barcode_img:
                try:
                    c.drawImage(
                        barcode_img,
                        -13*mm,
                        margin_top + 1*mm,
                        width=63*mm,
                        height=17*mm,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
                except Exception as e:
                    print(f"Erro ao desenhar código de barras: {e}")
        
        preco_texto = f"R$ {produto.preco_venda_novo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        c.setFont("Helvetica-Bold", 28)
        
        preco_width = c.stringWidth(preco_texto, "Helvetica-Bold", 28)
        x_preco = margin_left + 55*mm + (40*mm - preco_width) / 2
        c.drawString(x_preco, margin_top + 7*mm, preco_texto)
        
        c.setFont("Helvetica", 11)
        c.drawString(margin_left + 88*mm, margin_top + 2*mm, "UN")

    def gerar_pdf(self, produtos, output_path=None):
        if not produtos:
            raise ValueError("Nenhum produto fornecido para gerar etiquetas")
        
        if not output_path:
            data = datetime.now().strftime("%d%m%Y")
            
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            output_dir = os.path.join(base_dir, "etiquetas")
            os.makedirs(output_dir, exist_ok=True)
            
            if len(produtos) == 1:
                produto = produtos[0]
                descricao_limpa = "".join(c for c in produto.descricao if c.isalnum() or c in (' ', '-', '_')).strip()
                descricao_limpa = descricao_limpa.replace(' ', '_')[:50]
                filename = f"{descricao_limpa}_{produto.codigo}_{data}.pdf"
            else:
                filename = f"etiquetas_{data}.pdf"
            
            output_path = os.path.join(output_dir, filename)
        
        c = canvas.Canvas(output_path, pagesize=(self.ETIQUETA_WIDTH, self.ETIQUETA_HEIGHT))
        
        for i, produto in enumerate(produtos):
            codigo_barras = self._obter_codigo_barras(produto.codigo)
            
            self._desenhar_etiqueta(c, produto, 0, codigo_barras)
            
            if i < len(produtos) - 1:
                c.showPage()
        
        c.save()
        
        return output_path

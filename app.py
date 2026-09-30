from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# ============================================================
# COUNTER PENGUNJUNG
# ============================================================

COUNTER_FILE = 'visitor_count.json'


def get_visitor_count():
    """
    Mengambil jumlah pengunjung yang tersimpan.
    Jika file belum ada, otomatis dibuat dengan nilai 0.
    """
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'w') as f:
            json.dump({"count": 0}, f)

    try:
        with open(COUNTER_FILE, 'r') as f:
            data = json.load(f)

        return data.get("count", 0)

    except (json.JSONDecodeError, OSError):
        return 0


def increase_visitor_count():
    """
    Menambah jumlah pengunjung sebanyak 1
    setiap kali halaman utama dibuka.
    """
    count = get_visitor_count() + 1

    with open(COUNTER_FILE, 'w') as f:
        json.dump({"count": count}, f)

    return count


# ============================================================
# MASTER BATASAN SESUAI REGULASI BPOM & BEA CUKAI
# ============================================================

LIMITS = {
    "kosmetik": {
        "limit": 20,
        "unit": "pcs",
        "name": "Kosmetik"
    },
    "suplemen": {
        "limit": 5,
        "unit": "pcs",
        "name": "Suplemen Kesehatan / Obat Bahan Alam / Obat Kuasi"
    },
    "obat_tradisional": {
        "limit": 5,
        "unit": "pcs",
        "name": "Obat Bahan Alam / Obat Kuasi / Obat Tradisional"
    },
    "makanan": {
        "limit": 5,
        "unit": "kg",
        "name": "Pangan Olahan Lain (Kecuali Minuman Beralkohol)"
    },
    "tablet_kapsul": {
        "limit": 30,
        "unit": "pcs",
        "name": "Obat Sediaan Padat (Tablet / Kapsul)"
    },
    "krim_cairan_aerosol": {
        "limit": 3,
        "unit": "pcs",
        "name": "Obat Sediaan Semipadat, Cairan, dan Aerosol"
    }
}


# ============================================================
# OPSI MENU UTAMA KATEGORI
# ============================================================

MAIN_OPTIONS = [
    {"id": "obat", "icon": "💊", "text": "Obat"},
    {"id": "obat_tradisional", "icon": "🌿", "text": "Obat Tradisional"},
    {"id": "suplemen", "icon": "💪🏻", "text": "Suplemen Kesehatan"},
    {"id": "kosmetik", "icon": "💄", "text": "Kosmetika"},
    {
        "id": "pkmk",
        "icon": "🏥",
        "text": "Pangan Olahan Medis Khusus (PKMK)"
    },
    {
        "id": "makanan",
        "icon": "🧃",
        "text": "Pangan Olahan Lain",
        "note": "kecuali minuman beralkohol"
    }
]


# ============================================================
# OPSI SETELAH HASIL
# ============================================================

AFTER_ACTION_OPTIONS = [
    {"id": "check_another", "text": "🔄 Cek Barang Lain"},
    {"id": "finish", "text": "✅ Selesai"}
]


# ============================================================
# HALAMAN UTAMA
# ============================================================

@app.route('/')
def index():
    # Tambah jumlah pengunjung setiap kali halaman utama dibuka
    visitor_count = increase_visitor_count()

    return render_template(
        'index.html',
        visitor_count=visitor_count
    )


# ============================================================
# API MENU UTAMA
# ============================================================

@app.route('/api/main_menu', methods=['GET'])
def main_menu():
    return jsonify({
        "type": "question",
        "message": "Silakan pilih kategori barang berikutnya yang ingin Anda cek:",
        "options": MAIN_OPTIONS
    })


# ============================================================
# API PILIH KATEGORI
# ============================================================

@app.route('/api/select_category', methods=['POST'])
def select_category():
    data = request.json
    cat = data.get('category')

    if cat == 'obat':
        return jsonify({
            "type": "question",
            "message": "Anda memilih Obat. **Pilih jenis obat yang Anda bawa:**",
            "options": [
                {
                    "id": "narkotika",
                    "text": "Narkotika"
                },
                {
                    "id": "psikotropika",
                    "text": "Psikotropika"
                },
                {
                    "id": "tablet_kapsul",
                    "text": "Obat Sediaan Padat (Tablet/Kapsul)"
                },
                {
                    "id": "krim_cairan_aerosol",
                    "text": "Obat Sediaan Semipadat, Cairan, & Aerosol"
                }
            ]
        })

    elif cat == 'pkmk':
        return jsonify({
            "type": "question_bool",
            "item_key": "pkmk",
            "title": "Produk Pangan Olahan untuk Keperluan Medis Khusus (PKMK)",
            "message": "Apakah Anda membawa **Resep Dokter** untuk produk PKMK ini?",
            "options": [
                {
                    "id": "pkmk_ya",
                    "text": "Ya, membawa resep dokter"
                },
                {
                    "id": "pkmk_tidak",
                    "text": "Tidak membawa resep dokter"
                }
            ]
        })

    elif cat in LIMITS:
        item = LIMITS[cat]

        return jsonify({
            "type": "input_quantity",
            "item_key": cat,
            "title": item["name"],
            "message": (
                f"Masukkan jumlah **{item['name']}** "
                f"yang Anda bawa (dalam {item['unit']}):"
            )
        })

    return jsonify({
        "type": "error",
        "message": "Pilihan tidak valid."
    })


# ============================================================
# API PILIH JENIS OBAT
# ============================================================

@app.route('/api/select_drug_type', methods=['POST'])
def select_drug_type():
    data = request.json
    drug_type = data.get('drug_type')

    if drug_type == 'narkotika':
        return jsonify({
            "type": "result_popup",
            "status": "danger",
            "title": "🚫 TIDAK DIPERBOLEHKAN MASUK",
            "message": (
                "Pembawaan Narkotika **sama sekali tidak diperbolehkan** "
                "bagi penumpang."
            ),
            "actions": AFTER_ACTION_OPTIONS
        })

    elif drug_type == 'psikotropika':
        return jsonify({
            "type": "question_psikotropika",
            "message": (
                "Untuk Psikotropika, batasan aturan:\n"
                "• **Hanya WNA atau wisatawan asing**\n"
                "• Berapapun jumlahnya **harus sesuai resep dokter** "
                "(maksimal 60 hari pengobatan)\n\n"
                "Apakah Anda WNA/Wisatawan Asing & membawa resep dokter?"
            ),
            "options": [
                {
                    "id": "psiko_ya",
                    "text": "Ya, WNA & Ada Resep Dokter"
                },
                {
                    "id": "psiko_tidak",
                    "text": "Tidak Memiliki Resep"
                }
            ]
        })

    elif drug_type in LIMITS:
        item = LIMITS[drug_type]

        return jsonify({
            "type": "input_quantity",
            "item_key": drug_type,
            "title": item["name"],
            "message": (
                f"Masukkan jumlah **{item['name']}** "
                f"yang Anda bawa (dalam {item['unit']}):"
            )
        })

    return jsonify({
        "type": "error",
        "message": "Jenis obat tidak valid."
    })


# ============================================================
# API VALIDASI INPUT
# ============================================================

@app.route('/api/validate_input', methods=['POST'])
def validate_input():
    data = request.json
    item_key = data.get('item_key')

    # --------------------------------------------------------
    # Validasi Psikotropika
    # --------------------------------------------------------

    if item_key == 'psikotropika_check':
        is_valid = data.get('is_valid')

        if is_valid:
            return jsonify({
                "type": "result_popup",
                "status": "success",
                "title": "✅ DIPERSILAHKAN MASUK",
                "message": (
                    "Psikotropika diperbolehkan masuk khusus "
                    "WNA/wisatawan asing sesuai resep dokter "
                    "(maksimal 60 hari pengobatan)."
                ),
                "actions": AFTER_ACTION_OPTIONS
            })

        else:
            return jsonify({
                "type": "result_popup",
                "status": "danger",
                "title": "🚫 TIDAK DIPERBOLEHKAN MASUK",
                "message": (
                    "Psikotropika **tidak diperbolehkan masuk** "
                    "jika Anda bukan WNA/wisatawan asing atau "
                    "tanpa resep dokter."
                ),
                "actions": AFTER_ACTION_OPTIONS
            })

    # --------------------------------------------------------
    # Validasi PKMK
    # --------------------------------------------------------

    if item_key == 'pkmk':
        has_prescription = data.get('has_prescription')

        if has_prescription:
            return jsonify({
                "type": "result_popup",
                "status": "success",
                "title": "✅ DIPERSILAHKAN MASUK",
                "message": (
                    "Produk PKMK diperbolehkan masuk sesuai "
                    "dengan resep dokter yang dibawa."
                ),
                "actions": AFTER_ACTION_OPTIONS
            })

        else:
            return jsonify({
                "type": "result_popup",
                "status": "danger",
                "title": "🚫 TIDAK DIPERBOLEHKAN MASUK",
                "message": (
                    "Produk PKMK **wajib sesuai dengan resep dokter**. "
                    "Barang tidak diperbolehkan masuk tanpa resep."
                ),
                "actions": AFTER_ACTION_OPTIONS
            })

    # --------------------------------------------------------
    # Validasi Berdasarkan Jumlah
    # --------------------------------------------------------

    if item_key in LIMITS:
        item = LIMITS[item_key]

        try:
            qty = float(data.get('quantity', 0))
        except (ValueError, TypeError):
            qty = 0

        limit = item["limit"]
        unit = item["unit"]

        # ----------------------------------------------------
        # Jumlah tidak melebihi batas
        # ----------------------------------------------------

        if qty <= limit:
            return jsonify({
                "type": "result_popup",
                "status": "success",
                "title": "✅ DIPERSILAHKAN MASUK",
                "message": (
                    f"Jumlah **"
                    f"{int(qty) if qty.is_integer() else qty} "
                    f"{unit} {item['name']}** "
                    f"tidak melebihi batasan maksimal "
                    f"({limit} {unit})."
                ),
                "actions": AFTER_ACTION_OPTIONS
            })

        # ----------------------------------------------------
        # Jumlah melebihi batas
        # ----------------------------------------------------

        else:
            excess = qty - limit

            # Obat tablet/kapsul atau krim/cairan/aerosol
            if item_key in [
                'tablet_kapsul',
                'krim_cairan_aerosol'
            ]:
                return jsonify({
                    "type": "result_popup",
                    "status": "warning",
                    "title": "⚠️ MELEBIHI BATAS TANPA RESEP",
                    "message": (
                        f"Anda membawa **"
                        f"{int(qty) if qty.is_integer() else qty} "
                        f"{unit}** "
                        f"(Batas tanpa resep dokter: "
                        f"{limit} {unit}).\n\n"
                        f"• Jika **membawa resep dokter**: "
                        f"Dipersilahkan masuk "
                        f"(maksimal 90 hari pengobatan).\n"
                        f"• Jika **tanpa resep dokter**: "
                        f"Silakan **kurangi Jumlah sebanyak "
                        f"{int(excess) if excess.is_integer() else excess} "
                        f"{unit}** "
                        f"(hanya {limit} {unit} yang diperbolehkan)."
                    ),
                    "actions": AFTER_ACTION_OPTIONS
                })

            # Kategori lainnya
            else:
                return jsonify({
                    "type": "result_popup",
                    "status": "warning",
                    "title": "⚠️ PERINGATAN / KURANGI JUMLAH",
                    "message": (
                        f"Jumlah **"
                        f"{int(qty) if qty.is_integer() else qty} "
                        f"{unit}** "
                        f"melebihi batas maksimal pembawaan "
                        f"({limit} {unit} per penumpang).\n\n"
                        f"👉 Silakan kurangi Jumlah Anda sebanyak "
                        f"**{int(excess) if excess.is_integer() else excess} "
                        f"{unit}** "
                        f"agar tidak melebihi batasan "
                        f"{limit} {unit}."
                    ),
                    "excess": excess,
                    "actions": AFTER_ACTION_OPTIONS
                })

    # --------------------------------------------------------
    # Jika terjadi kesalahan
    # --------------------------------------------------------

    return jsonify({
        "type": "error",
        "message": "Terjadi kesalahan sistem."
    })


# ============================================================
# MENJALANKAN APLIKASI
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
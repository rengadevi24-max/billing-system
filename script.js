const API_BASE = '/api';

let items = [];
let selectedRow = null;

function fmt(n) { return '₹' + Number(n || 0).toFixed(2); }

function renderItems() {
  const body = document.getElementById('itemsBody');
  body.innerHTML = '';
  items.forEach((item, idx) => {
    const tr = document.createElement('tr');
    tr.dataset.idx = idx;
    if (selectedRow === idx) tr.classList.add('selected');
    tr.onclick = () => { selectedRow = idx; renderItems(); };
    tr.innerHTML =
      '<td class="row-num">' + (idx + 1) + '</td>' +
      '<td><input value="' + item.sku + '" onchange="updateItem(' + idx + ',\'sku\',this.value)"></td>' +
      '<td><input value="' + item.name + '" onchange="updateItem(' + idx + ',\'name\',this.value)"></td>' +
      '<td class="num"><input type="number" min="1" step="1" style="text-align:right" value="' + item.qty + '" onchange="updateItem(' + idx + ',\'qty\',this.value)"></td>' +
      '<td class="num"><input type="number" min="0" step="0.01" style="text-align:right" value="' + item.price + '" onchange="updateItem(' + idx + ',\'price\',this.value)"></td>' +
      '<td class="line-total">' + fmt(item.qty * item.price) + '</td>';
    body.appendChild(tr);
  });
  document.getElementById('lineCount').textContent = items.length;
  calcTotals();
}

function updateItem(idx, field, value) {
  if (field === 'qty' || field === 'price') value = parseFloat(value) || 0;
  items[idx][field] = value;
  renderItems();
}

function addLine() {
  items.push({ sku: '', name: '', qty: 1, price: 0 });
  selectedRow = items.length - 1;
  renderItems();
}

async function addItemFromList() {
  try {
    const res = await fetch(API_BASE + '/products', { credentials: 'include' });
    if (!res.ok) throw new Error('Server error');
    const products = await res.json();

    if (!products.length) {
      alert('No products found in database. Add products via /api/products first.');
      return;
    }

    let listText = '';
    products.forEach((p, i) => {
      listText += (i + 1) + '. ' + p.name + '  (SKU: ' + p.sku + ', Rs.' + p.price + ')\n';
    });
    const choice = prompt('Select a product by number:\n\n' + listText);
    const idx = parseInt(choice) - 1;

    if (isNaN(idx) || idx < 0 || idx >= products.length) return;

    const p = products[idx];
    items.push({ sku: p.sku, name: p.name, qty: 1, price: parseFloat(p.price) });
    selectedRow = items.length - 1;
    renderItems();
  } catch (err) {
    alert('Could not reach backend server. Make sure the Flask server is running\n\n(' + err.message + ')');
  }
}

async function selectCustomer() {
  try {
    const res = await fetch(API_BASE + '/customers', { credentials: 'include' });
    if (!res.ok) throw new Error('Server error');
    const customers = await res.json();

    if (!customers.length) {
      alert('No customers found in database yet.');
      return;
    }

    let listText = '';
    customers.forEach((c, i) => {
      listText += (i + 1) + '. ' + c.name + '  (' + (c.email || 'no email') + ')\n';
    });
    const choice = prompt('Select a customer by number:\n\n' + listText);
    const idx = parseInt(choice) - 1;

    if (isNaN(idx) || idx < 0 || idx >= customers.length) return;

    const c = customers[idx];
    document.getElementById('soldId').textContent = String(c.id).padStart(8, '0');
    document.getElementById('soldName').value = c.name;
    document.getElementById('soldAddress').value = c.address || '';
    document.getElementById('custEmail').value = c.email || '';
    syncShipTo();
  } catch (err) {
    alert('Could not reach backend server. Make sure the Flask server is running\n\n(' + err.message + ')');
  }
}

function editSelected() {
  if (selectedRow === null) { alert('Select a line first by clicking on a row.'); return; }
  const row = document.querySelectorAll('#itemsBody tr')[selectedRow];
  row.querySelector('input').focus();
}

function deleteLine() {
  if (selectedRow === null) { alert('Select a line first by clicking on a row.'); return; }
  items.splice(selectedRow, 1);
  selectedRow = null;
  renderItems();
}

function syncShipTo() {
  const same = document.getElementById('sameAsSold').checked;
  const shipName = document.getElementById('shipName');
  const shipAddress = document.getElementById('shipAddress');
  if (same) {
    shipName.value = document.getElementById('soldName').value;
    shipAddress.value = document.getElementById('soldAddress').value;
    shipName.disabled = true;
    shipAddress.disabled = true;
  } else {
    shipName.disabled = false;
    shipAddress.disabled = false;
  }
}

function calcTotals() {
  const subTotal = items.reduce((sum, i) => sum + (i.qty * i.price), 0);
  const discountPct = parseFloat(document.getElementById('discount').value) || 0;
  const taxRate = parseFloat(document.getElementById('taxRate').value) || 0;
  const delivery = parseFloat(document.getElementById('delivery').value) || 0;
  const payments = parseFloat(document.getElementById('payments').value) || 0;

  const discountAmt = subTotal * (discountPct / 100);
  const taxable = subTotal - discountAmt;
  const taxAmt = taxable * (taxRate / 100);
  const invoiceTotal = taxable + taxAmt + delivery;
  const amountDue = invoiceTotal - payments;

  document.getElementById('subTotal').textContent = fmt(subTotal);
  document.getElementById('invoiceTotal').textContent = fmt(invoiceTotal);
  document.getElementById('amountDue').textContent = fmt(amountDue);
}

async function doLogout() {
  try {
    await fetch(API_BASE + '/logout', {
      method: 'POST',
      credentials: 'include',
    });
  } catch (err) {
    // ignore network errors on logout
  }
  window.location.href = 'login.html';
}

async function checkSession() {
  try {
    const res = await fetch(API_BASE + '/session', { credentials: 'include' });
    const data = await res.json();
    if (!data.logged_in) {
      window.location.href = 'login.html';
      return;
    }
    if (data.store_name) {
      document.getElementById('companyName').value = data.store_name;
    }
  } catch (err) {
    // if backend not reachable, let the page load normally
  }
}

function todayStr() {
  return new Date().toISOString().split('T')[0];
}

function openStockDetails() {
  window.open('stock-details.html?date=' + todayStr(), '_blank');
}

async function loadDailySummary() {
  try {
    const res = await fetch(API_BASE + '/daily-summary/' + todayStr(), { credentials: 'include' });
    if (!res.ok) throw new Error('Server error');
    const data = await res.json();
    document.getElementById('summaryTotalSales').textContent = fmt(data.total_sales);
    document.getElementById('summaryStockSold').textContent = data.stock_sold;
    document.getElementById('summaryStockReorder').value = data.stock_to_reorder;
  } catch (err) {
    // silently ignore if backend not reachable yet on page load
  }
}

async function saveStockReorder() {
  const value = parseInt(document.getElementById('summaryStockReorder').value) || 0;
  try {
    const res = await fetch(API_BASE + '/daily-summary/' + todayStr(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ stock_to_reorder: value }),
    });
    if (!res.ok) throw new Error('Server error');
    alert('Stock to reorder saved: ' + value);
  } catch (err) {
    alert('Could not reach backend server. Make sure the Flask server is running\n\n(' + err.message + ')');
  }
}

function markPaid() {
  document.getElementById('payments').value = document.getElementById('invoiceTotal').textContent.replace('₹','');
  calcTotals();
  alert('Invoice marked as PAID.');
}
function editPayments() { document.getElementById('payments').focus(); }
function openCalculator() { alert('Calculator: use the Sub total, Tax %, Discount and Delivery fields — totals update automatically.'); }
async function saveClose() {
  const payload = {
    invoice_no: document.getElementById('invoiceNo').value,
    customer_name: document.getElementById('soldName').value,
    customer_address: document.getElementById('soldAddress').value,
    customer_email: document.getElementById('custEmail').value,
    ship_name: document.getElementById('shipName').value,
    ship_address: document.getElementById('shipAddress').value,
    invoice_date: document.getElementById('invDate').value,
    due_date: document.getElementById('dueDate').value,
    terms: document.getElementById('terms').value,
    order_no: document.getElementById('orderNo').value,
    sales_rep: document.getElementById('salesRep').value,
    tracking: document.getElementById('tracking').value,
    sub_total: parseFloat(document.getElementById('subTotal').textContent.replace('₹', '')) || 0,
    discount_pct: parseFloat(document.getElementById('discount').value) || 0,
    tax_pct: parseFloat(document.getElementById('taxRate').value) || 0,
    delivery_cost: parseFloat(document.getElementById('delivery').value) || 0,
    invoice_total: parseFloat(document.getElementById('invoiceTotal').textContent.replace('₹', '')) || 0,
    payments: parseFloat(document.getElementById('payments').value) || 0,
    amount_due: parseFloat(document.getElementById('amountDue').textContent.replace('₹', '')) || 0,
    printed_date: document.getElementById('printedDate').value,
    emailed_date: document.getElementById('emailedDate').value,
    template: document.getElementById('templateSelect').value,
    comments: document.getElementById('commentsText').value,
    private_comments: document.getElementById('privateCommentsText').value,
    terms_conditions: document.getElementById('termsConditionsText').value,
    footer_text: document.getElementById('footerText').value,
    is_recurring: document.getElementById('isRecurring').checked,
    items: items.map(i => ({
      sku: i.sku,
      item_name: i.name,
      qty: i.qty,
      price: i.price,
      line_total: i.qty * i.price,
    })),
  };

  try {
    const res = await fetch(API_BASE + '/invoices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      alert('Error saving invoice: ' + (data.error || 'Unknown error'));
      return;
    }
    alert('Invoice saved to database!\n\nInvoice No: ' + payload.invoice_no + '\nAmount Due: ' + fmt(payload.amount_due));
    loadDailySummary();
  } catch (err) {
    alert('Could not reach backend server. Make sure the Flask server is running\n\n(' + err.message + ')');
  }
}
function updatePrintFields() {
  const companyName = document.getElementById('companyName').value;
  document.getElementById('printShopName').textContent = companyName;
  document.getElementById('printTotalAmount').textContent =
    document.getElementById('invoiceTotal').textContent;
}
window.addEventListener('beforeprint', updatePrintFields);

function previewInvoice() { window.print(); }
function emailInvoice() { alert('Invoice would be emailed to: ' + document.getElementById('custEmail').value); }

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('tabHeads').addEventListener('click', (e) => {
    if (e.target.tagName !== 'BUTTON') return;
    document.querySelectorAll('.tab-heads button').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    ['status','comments','private','terms','footer','recurring'].forEach(t => {
      document.getElementById('tab-' + t).style.display = (t === e.target.dataset.tab) ? 'block' : 'none';
    });
  });

  // init dates to today
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('invDate').value = today;
  document.getElementById('printedDate').value = today;
  document.getElementById('emailedDate').value = today;

  renderItems();
  syncShipTo();
  loadDailySummary();
  checkSession();
});
const state = {
    page: 0,
    pageSize: 25,
    totalRows: 0,
    pivotRows: "customer_name",
    pivotColumns: "order_month",
    pivotMetric: "revenue",
};

const summaryDescriptors = [
    { key: "total_revenue", label: "Tổng doanh số", type: "currency", hint: "Doanh số từ order details" },
    { key: "avg_order_value", label: "Giá trị đơn TB", type: "currency", hint: "Doanh số / số đơn hàng" },
    { key: "order_count", label: "Số đơn hàng", type: "number", hint: "Đơn hàng thỏa điều kiện lọc" },
    { key: "customer_count", label: "Khách hàng", type: "number", hint: "Khách hàng phát sinh doanh số" },
    { key: "product_count", label: "Mặt hàng", type: "number", hint: "Sản phẩm xuất hiện trong kết quả" },
    { key: "total_quantity", label: "Tổng số lượng", type: "number", hint: "Tổng quantity ordered" },
];

document.addEventListener("DOMContentLoaded", async () => {
    bindEvents();
    renderSummaryCards({});
    renderEmpty("customer-chart", "Chưa có dữ liệu biểu đồ.");
    renderEmpty("timeline-chart", "Chưa có dữ liệu biểu đồ.");
    renderEmpty("line-chart", "Chưa có dữ liệu biểu đồ.");
    renderEmpty("pivot-table", "Chưa có dữ liệu pivot.");
    renderEmpty("customer-results", "Nhập từ khóa để tìm khách hàng.");
    renderEmpty("product-results", "Nhập từ khóa để tìm mặt hàng.");

    try {
        await loadMetadata();
        await refreshDashboard();
    } catch (error) {
        setStatus(error.message);
    }
});

function bindEvents() {
    document.getElementById("filters-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        state.page = 0;
        await refreshDashboard();
    });

    document.getElementById("btn-reset").addEventListener("click", async () => {
        document.getElementById("filters-form").reset();
        state.page = 0;
        await refreshDashboard();
    });

    document.getElementById("btn-search-customers").addEventListener("click", searchCustomers);
    document.getElementById("btn-search-products").addEventListener("click", searchProducts);
    document.getElementById("btn-refresh-pivot").addEventListener("click", renderPivotFromCurrentState);

    document.getElementById("pivot-rows").addEventListener("change", (event) => {
        state.pivotRows = event.target.value;
    });
    document.getElementById("pivot-columns").addEventListener("change", (event) => {
        state.pivotColumns = event.target.value;
    });
    document.getElementById("pivot-metric").addEventListener("change", (event) => {
        state.pivotMetric = event.target.value;
    });

    document.getElementById("btn-prev-page").addEventListener("click", async () => {
        if (state.page === 0) {
            return;
        }
        state.page -= 1;
        await loadDetailsOnly();
    });

    document.getElementById("btn-next-page").addEventListener("click", async () => {
        const nextOffset = (state.page + 1) * state.pageSize;
        if (nextOffset >= state.totalRows) {
            return;
        }
        state.page += 1;
        await loadDetailsOnly();
    });
}

async function loadMetadata() {
    const data = await fetchJson("/api/metadata");
    populateSelect("product-line-filter", data.product_lines);
    populateSelect("country-filter", data.countries);
    populateSelect("status-filter", data.statuses);
}

function populateSelect(selectId, values) {
    const select = document.getElementById(selectId);
    const current = select.value;
    const options = [`<option value="">Tất cả</option>`]
        .concat(values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`));
    select.innerHTML = options.join("");
    if (values.includes(current)) {
        select.value = current;
    }
}

async function searchCustomers() {
    const keyword = document.getElementById("customer-search").value.trim();
    const country = document.getElementById("country-filter").value;
    const query = new URLSearchParams({ q: keyword, limit: "12" });
    if (country) {
        query.set("country", country);
    }
    const data = await fetchJson(`/api/customers?${query.toString()}`);
    const container = document.getElementById("customer-results");
    if (!data.items.length) {
        renderEmpty("customer-results", "Không tìm thấy khách hàng phù hợp.");
        return;
    }
    container.innerHTML = data.items.map((item) => `
        <article class="result-item">
            <strong>${escapeHtml(item.customer_name)}</strong>
            <div class="result-meta">
                Mã KH: ${item.customer_number}<br>
                Liên hệ: ${escapeHtml(item.contact_name)}<br>
                ${escapeHtml(item.city)}, ${escapeHtml(item.country)}<br>
                ${escapeHtml(item.phone)}${item.sales_rep ? `<br>Sales rep: ${escapeHtml(item.sales_rep)}` : ""}
            </div>
        </article>
    `).join("");
}

async function searchProducts() {
    const keyword = document.getElementById("product-search").value.trim();
    const productLine = document.getElementById("product-line-filter").value;
    const query = new URLSearchParams({ q: keyword, limit: "12" });
    if (productLine) {
        query.set("product_line", productLine);
    }
    const data = await fetchJson(`/api/products?${query.toString()}`);
    const container = document.getElementById("product-results");
    if (!data.items.length) {
        renderEmpty("product-results", "Không tìm thấy mặt hàng phù hợp.");
        return;
    }
    container.innerHTML = data.items.map((item) => `
        <article class="result-item">
            <strong>${escapeHtml(item.product_name)}</strong>
            <div class="result-meta">
                Mã SP: ${escapeHtml(item.product_code)}<br>
                Dòng SP: ${escapeHtml(item.product_line)}<br>
                Vendor: ${escapeHtml(item.product_vendor)}<br>
                Tồn kho: ${formatNumber(item.quantity_in_stock)} · Giá vốn: ${formatCurrency(item.buy_price)} · MSRP: ${formatCurrency(item.msrp)}
            </div>
        </article>
    `).join("");
}

async function refreshDashboard() {
    setStatus("Đang tải dashboard từ REST API...");
    const filters = collectFilters();
    const query = buildQuery(filters);
    const detailQuery = buildQuery({ ...filters, limit: state.pageSize, offset: state.page * state.pageSize });

    const [summary, charts, details, pivot] = await Promise.all([
        fetchJson(`/api/dashboard/summary?${query}`),
        fetchJson(`/api/dashboard/charts?${query}`),
        fetchJson(`/api/dashboard/details?${detailQuery}`),
        fetchJson(`/api/dashboard/pivot?${buildQuery({ ...filters, limit: 1500 })}`),
    ]);

    window.currentPivotData = pivot.items;
    renderSummaryCards(summary);
    renderCharts(charts);
    renderDetails(details);
    renderPivot(pivot.items);
    setStatus("Dữ liệu đã được cập nhật.");
}

async function loadDetailsOnly() {
    const filters = collectFilters();
    const detailQuery = buildQuery({ ...filters, limit: state.pageSize, offset: state.page * state.pageSize });
    const details = await fetchJson(`/api/dashboard/details?${detailQuery}`);
    renderDetails(details);
}

function renderSummaryCards(summary) {
    const container = document.getElementById("summary-cards");
    container.innerHTML = summaryDescriptors.map((descriptor) => {
        const rawValue = summary[descriptor.key] ?? 0;
        const value = descriptor.type === "currency" ? formatCurrency(rawValue) : formatNumber(rawValue);
        return `
            <article class="summary-card">
                <span class="label">${descriptor.label}</span>
                <strong class="value">${value}</strong>
                <span class="hint">${descriptor.hint}</span>
            </article>
        `;
    }).join("");
}

function renderCharts(data) {
    renderBarChart("customer-chart", data.customer_sales, formatCurrency);
    renderLineChart("timeline-chart", data.monthly_sales);
    renderDonutChart("line-chart", data.product_line_sales);
}

function renderBarChart(containerId, items, formatter) {
    if (!items || !items.length) {
        renderEmpty(containerId, "Không có dữ liệu doanh số theo khách hàng.");
        return;
    }
    const maxValue = Math.max(...items.map((item) => item.value), 1);
    const html = `
        <div class="bar-list">
            ${items.map((item) => `
                <div class="bar-row">
                    <div class="bar-meta">
                        <span>${escapeHtml(item.label)}</span>
                        <strong>${formatter(item.value)}</strong>
                    </div>
                    <div class="bar-track">
                        <div class="bar-fill" style="width:${(item.value / maxValue) * 100}%"></div>
                    </div>
                </div>
            `).join("")}
        </div>
    `;
    document.getElementById(containerId).innerHTML = html;
}

function renderLineChart(containerId, items) {
    if (!items || !items.length) {
        renderEmpty(containerId, "Không có dữ liệu doanh số theo thời gian.");
        return;
    }

    const width = 640;
    const height = 220;
    const padding = 28;
    const values = items.map((item) => item.revenue);
    const maxValue = Math.max(...values, 1);
    const step = items.length > 1 ? (width - padding * 2) / (items.length - 1) : 0;

    const points = items.map((item, index) => {
        const x = padding + index * step;
        const y = height - padding - ((item.revenue / maxValue) * (height - padding * 2));
        return { x, y, label: item.label, revenue: item.revenue, quantity: item.quantity };
    });

    const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
    const gridLines = [0.25, 0.5, 0.75].map((ratio) => {
        const y = height - padding - ((height - padding * 2) * ratio);
        return `<line class="line-grid" x1="${padding}" y1="${y}" x2="${width - padding}" y2="${y}"></line>`;
    }).join("");

    const html = `
        <div class="line-chart-shell">
            <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Biểu đồ xu hướng doanh số">
                ${gridLines}
                <path class="line-path" d="${path}"></path>
                ${points.map((point) => `<circle class="line-dot" cx="${point.x}" cy="${point.y}" r="4.5"></circle>`).join("")}
            </svg>
            <div class="line-labels">
                ${points.map((point) => `<span>${escapeHtml(point.label)}: ${formatCurrency(point.revenue)} / ${formatNumber(point.quantity)}</span>`).join("")}
            </div>
        </div>
    `;
    document.getElementById(containerId).innerHTML = html;
}

function renderDonutChart(containerId, items) {
    if (!items || !items.length) {
        renderEmpty(containerId, "Không có cơ cấu dòng sản phẩm.");
        return;
    }

    const palette = ["#1f6a74", "#b14d1f", "#ddb15c", "#467d42", "#6d4ba8", "#d76d77", "#3b82f6"];
    const total = items.reduce((sum, item) => sum + item.value, 0) || 1;
    const radius = 72;
    const circumference = 2 * Math.PI * radius;
    let offset = 0;

    const segments = items.map((item, index) => {
        const length = (item.value / total) * circumference;
        const segment = {
            color: palette[index % palette.length],
            dasharray: `${length} ${circumference - length}`,
            dashoffset: -offset,
            label: item.label,
            value: item.value,
        };
        offset += length;
        return segment;
    });

    const html = `
        <div class="donut-shell">
            <svg viewBox="0 0 220 220" role="img" aria-label="Biểu đồ cơ cấu doanh số">
                <circle cx="110" cy="110" r="${radius}" fill="none" stroke="rgba(31, 106, 116, 0.08)" stroke-width="26"></circle>
                ${segments.map((segment) => `
                    <circle
                        cx="110"
                        cy="110"
                        r="${radius}"
                        fill="none"
                        stroke="${segment.color}"
                        stroke-width="26"
                        stroke-linecap="round"
                        stroke-dasharray="${segment.dasharray}"
                        stroke-dashoffset="${segment.dashoffset}"
                        transform="rotate(-90 110 110)"
                    ></circle>
                `).join("")}
                <text x="110" y="104" text-anchor="middle" font-size="16" fill="#6f5a48">Tổng doanh số</text>
                <text x="110" y="128" text-anchor="middle" font-size="22" font-weight="700" fill="#2d1f14">${formatCompactCurrency(total)}</text>
            </svg>
            <div class="legend-list">
                ${segments.map((segment) => `
                    <div class="legend-item">
                        <span class="legend-swatch" style="background:${segment.color}"></span>
                        <span>${escapeHtml(segment.label)}</span>
                        <strong>${formatCurrency(segment.value)}</strong>
                    </div>
                `).join("")}
            </div>
        </div>
    `;
    document.getElementById(containerId).innerHTML = html;
}

function renderDetails(data) {
    state.totalRows = data.total_rows;
    const tbody = document.getElementById("details-body");
    if (!data.items.length) {
        tbody.innerHTML = `<tr><td colspan="10"><div class="empty-state">Không có dữ liệu chi tiết theo bộ lọc hiện tại.</div></td></tr>`;
        document.getElementById("detail-range").textContent = "0 dòng";
        return;
    }

    tbody.innerHTML = data.items.map((item) => `
        <tr>
            <td>${escapeHtml(item.order_date)}</td>
            <td>#${item.order_number}</td>
            <td>${escapeHtml(item.customer_name)}</td>
            <td>${escapeHtml(item.country)}</td>
            <td>${escapeHtml(item.product_name)}</td>
            <td>${escapeHtml(item.product_line)}</td>
            <td>${escapeHtml(item.status)}</td>
            <td class="numeric">${formatNumber(item.quantity)}</td>
            <td class="numeric">${formatCurrency(item.unit_price)}</td>
            <td class="numeric">${formatCurrency(item.revenue)}</td>
        </tr>
    `).join("");

    const start = state.page * state.pageSize + 1;
    const end = Math.min((state.page + 1) * state.pageSize, state.totalRows);
    document.getElementById("detail-range").textContent = `${start}-${end} / ${formatNumber(state.totalRows)} dòng`;
}

function renderPivotFromCurrentState() {
    renderPivot(window.currentPivotData || []);
}

function renderPivot(items) {
    const container = document.getElementById("pivot-table");
    if (!items || !items.length) {
        renderEmpty("pivot-table", "Không có dữ liệu pivot theo bộ lọc hiện tại.");
        return;
    }

    const rowKey = state.pivotRows;
    const columnKey = state.pivotColumns;
    const metric = state.pivotMetric;
    const columnValues = [...new Set(items.map((item) => item[columnKey] || "N/A"))].sort();
    const rowValues = [...new Set(items.map((item) => item[rowKey] || "N/A"))].sort();
    const matrix = new Map();

    for (const item of items) {
        const rowValue = item[rowKey] || "N/A";
        const columnValue = item[columnKey] || "N/A";
        const cellKey = `${rowValue}__${columnValue}`;
        const current = matrix.get(cellKey) || 0;
        matrix.set(cellKey, current + Number(item[metric] || 0));
    }

    const bodyRows = rowValues.map((rowValue) => {
        const cells = columnValues.map((columnValue) => {
            const value = matrix.get(`${rowValue}__${columnValue}`) || 0;
            return {
                columnValue,
                value,
            };
        });
        const total = cells.reduce((sum, cell) => sum + cell.value, 0);
        return { rowValue, cells, total };
    });

    const footerTotals = columnValues.map((columnValue) => bodyRows.reduce((sum, row) => {
        const cell = row.cells.find((entry) => entry.columnValue === columnValue);
        return sum + (cell ? cell.value : 0);
    }, 0));
    const grandTotal = footerTotals.reduce((sum, value) => sum + value, 0);
    const formatter = metric === "revenue" ? formatCurrency : formatNumber;

    container.innerHTML = `
        <table class="pivot-table">
            <thead>
                <tr>
                    <th>${pivotLabel(rowKey)}</th>
                    ${columnValues.map((value) => `<th class="numeric">${escapeHtml(value)}</th>`).join("")}
                    <th class="numeric">Tổng</th>
                </tr>
            </thead>
            <tbody>
                ${bodyRows.map((row) => `
                    <tr>
                        <td>${escapeHtml(row.rowValue)}</td>
                        ${row.cells.map((cell) => `<td class="numeric">${formatter(cell.value)}</td>`).join("")}
                        <td class="numeric"><strong>${formatter(row.total)}</strong></td>
                    </tr>
                `).join("")}
            </tbody>
            <tfoot>
                <tr>
                    <td>Tổng cộng</td>
                    ${footerTotals.map((value) => `<td class="numeric">${formatter(value)}</td>`).join("")}
                    <td class="numeric">${formatter(grandTotal)}</td>
                </tr>
            </tfoot>
        </table>
    `;
}

function pivotLabel(key) {
    const labels = {
        customer_name: "Khách hàng",
        country: "Quốc gia",
        product_line: "Dòng sản phẩm",
        product_name: "Mặt hàng",
        status: "Trạng thái",
        order_month: "Tháng",
    };
    return labels[key] || key;
}

function collectFilters() {
    const form = document.getElementById("filters-form");
    const data = new FormData(form);
    return Object.fromEntries([...data.entries()].filter(([, value]) => value !== ""));
}

function buildQuery(params) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
            query.set(key, value);
        }
    });
    return query.toString();
}

async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Không thể tải dữ liệu từ ${url}`);
    }
    return response.json();
}

function renderEmpty(containerId, message) {
    document.getElementById(containerId).innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function setStatus(message) {
    document.getElementById("dashboard-status").textContent = message;
}

function formatCurrency(value) {
    return new Intl.NumberFormat("vi-VN", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
    }).format(Number(value || 0));
}

function formatCompactCurrency(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        notation: "compact",
        maximumFractionDigits: 1,
    }).format(Number(value || 0));
}

function formatNumber(value) {
    return new Intl.NumberFormat("vi-VN").format(Number(value || 0));
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#39;");
}

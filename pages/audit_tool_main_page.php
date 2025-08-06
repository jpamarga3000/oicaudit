<?php
// audit_tool_main_page.php - Combines content from Aging, Petty Cash, TRNM, GL, LNACC, SVACC, and now Trial Balance
?>
<div id="auditToolMainPage" class="tab-content active">
    <section id="agingConsolidatedSection" class="dashboard-section">
        <h3 class="section-title">Aging Consolidated</h3>
        <?php include 'aging_consolidated.php'; ?>
    </section>

    <section id="pettyCashSection" class="dashboard-section">
        <h3 class="section-title">Petty Cash</h3>
        <?php include 'petty_cash.php'; ?>
    </section>

    <section id="trnmMainSection" class="dashboard-section">
        <h3 class="section-title">TRNM Processing</h3>
        <?php include 'trnm_main.php'; ?>
    </section>

    <section id="glMainSection" class="dashboard-section">
        <h3 class="section-title">General Ledger Processing</h3>
        <?php include 'gl_main.php'; ?>
    </section>

    <section id="lnaccMainSection" class="dashboard-section">
        <h3 class="section-title">Loan Account Processing</h3>
        <?php include 'lnacc_main.php'; ?>
    </section>

    <section id="svaccMainSection" class="dashboard-section">
        <h3 class="section-title">Savings Account Processing</h3>
        <?php include 'svacc_main.php'; ?>
    </section>

    <section id="journalVoucherSection" class="dashboard-section">
        <h3 class="section-title">Journal Voucher</h3>
        <?php include 'journal_voucher.php'; ?>
    </section>

    <!-- NEW: Trial Balance Processing Section -->
    <section id="auditToolTbSection" class="dashboard-section">
        <h3 class="section-title">Trial Balance Processing</h3>
        <?php include 'audit_tool_tb.php'; ?>
    </section>

</div>

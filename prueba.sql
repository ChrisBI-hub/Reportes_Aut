SELECT
    [Tipo Operación Desc] as [Tipo de Operación],
    Importador,
    SABANA.[dFechaPago] as [Fecha de Pago],
    SABANA.[Aduana/Sección Despacho] as [Aduana/Sección Despacho],
    SABANA.Referencia,
    Pedimento as [Pedimento],
    SABANA.[Mercancía] as [Mercancía],
    SABANA.[Clave Pedimento] as [Clave Pedimento],
    CAST(CuentaG_FechaFactura AS DATETIME) AS [Fecha de factura],
    CONCAT(SUBSTRING(TRIM([CuentaG_Folio_Num_Factura]),1,1),TRIM([CuentaG_FolioFactura])) AS [No Factura],
    'ABSOLUTE BROKERAGE CUSTOMS, S.C.' AS [Proveedor],
    'HONORARIOS DE AGENCIA' AS [Descripcion del Gasto],
    TIMBRE.sUUID AS [UUID de la Factura],
    SubtotalCuentadeGastosServicioAA AS [Subtotal],
    IvaCuentadeGastos AS [IVA],
    0 AS [Retension],
    ISNULL(TotaldeGastos, SABANA.CuentaG_SaldoTotal) AS [Total]
FROM [Admin].SIR_VT_Sabana_Pedimento_ABC SABANA
LEFT JOIN [Admin].[ADMINO_15_CUENTAS_GASTOS] CUENTASG
    ON CONCAT(SUBSTRING(TRIM(SABANA.[CuentaG_Folio_Num_Factura]),1,1),TRIM(SABANA.[CuentaG_FolioFactura])) = CONCAT(CUENTASG.sPrefijo, CUENTASG.nNumero)
LEFT JOIN [Admin].[ADMINO_31_TIMBRE_FACTURA] TIMBRE
    ON CUENTASG.nIdCtaGastos15 = TIMBRE.nIdCtaGastos15
WHERE (Importador LIKE '%ORGANON%' OR Importador LIKE '%UNDRA%')
    AND YEAR(CuentaG_FechaFactura) = 2026
    AND MONTH(CuentaG_FechaFactura) = 07
    and [Clave Pedimento] = 'R1'
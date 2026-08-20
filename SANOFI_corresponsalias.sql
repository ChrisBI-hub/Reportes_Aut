/* QUERY TIEMPOS DE OPERACIÓN SANOFI SIN FINES DE SEMANA CON CLASIFICACIÓN PRODUCTIVO/NO PRODUCTIVO */
/* Ultima modificacion: [11/08/2026] */
/* Incluye clasificación de mercancías - CORREGIDO COLLATION */

WITH ClasificacionMercancias AS (

    SELECT DISTINCT
        [DESCRIPCIÓN_PRODUCTO] COLLATE SQL_Latin1_General_CP1_CI_AS AS [DESCRIPCIÓN_PRODUCTO],
        'PRODUCTIVO' AS Clasificacion
    FROM [BI].[dbo].[Track and Trace productivo]
    WHERE [DESCRIPCIÓN_PRODUCTO] IS NOT NULL 
      AND LTRIM(RTRIM([DESCRIPCIÓN_PRODUCTO])) <> ''
    
    UNION ALL
    
    -- No productivos
    SELECT DISTINCT
        [DESCRIPCIÓN_PRODUCTO] COLLATE SQL_Latin1_General_CP1_CI_AS AS [DESCRIPCIÓN_PRODUCTO],
        'NO PRODUCTIVO' AS Clasificacion
    FROM [BI].[dbo].[Track and Trace No productivo]
    WHERE [DESCRIPCIÓN_PRODUCTO] IS NOT NULL 
      AND LTRIM(RTRIM([DESCRIPCIÓN_PRODUCTO])) <> ''
),
RefEntradaPorPedimento AS (
    SELECT
        REPLACE(TRIM(Referencia), '/', '') AS ReferenciaNormalizada,
        RIGHT(TRIM(CAST(Pedimento AS VARCHAR(20))), 7) AS PedimentoUltimos7,
        MAX(NULLIF(TRIM(Mercancia), '')) AS MercanciaRefPedimento
    FROM [SIR].[Admin].[ADMIN_VT_CGReferenciaEntrada]
    GROUP BY
        REPLACE(TRIM(Referencia), '/', ''),
        RIGHT(TRIM(CAST(Pedimento AS VARCHAR(20))), 7)
),
RefEntradaPorReferencia AS (
    SELECT
        REPLACE(TRIM(Referencia), '/', '') AS ReferenciaNormalizada,
        MAX(NULLIF(TRIM(Mercancia), '')) AS MercanciaRefReferencia
    FROM [SIR].[Admin].[ADMIN_VT_CGReferenciaEntrada]
    GROUP BY REPLACE(TRIM(Referencia), '/', '')
),
ConsultaBase AS (
    SELECT
        Sucursal AS Sucursal,
        CASE
            WHEN Sucursal = 'CIUDAD DE MÉXICO' THEN 'AÉREO AICM'
            WHEN Sucursal = 'AIFA ESTADO DE MEXICO' THEN 'AÉREO AIFA'
            WHEN Sucursal = 'VERACRUZ' THEN 'MARÍTIMO VERACRUZ'
            WHEN CHARINDEX('LT', Referencia) > 0 THEN 'LAREDO'
            WHEN CHARINDEX('MNS', Referencia) > 0 THEN 'MANZANILLO'
            ELSE 'CORRESPONSALIAS'
        END AS [Tipo Sucursal],
        Referencia,
        Pedimento,
        [Aduana/Sección Despacho],
        

        [ Fecha de Pago],
        
        CASE
            WHEN Sucursal = 'CORRESPONSALIAS' THEN MONTH([Corresponsalias Fecha de Pago])
            ELSE MONTH([ Fecha de Pago])
        END AS "MES",
        [Fechas de Cuentas de Gastos],
        [Fecha Entrada/Presentación],
        
        /*---------------Función de Fecha de pago---------------*/
        CONVERT(VARCHAR(10),
        CASE
            WHEN Sucursal = 'CORRESPONSALIAS' THEN [Corresponsalias Fecha de Pago]
            WHEN Sucursal <> 'CORRESPONSALIAS' THEN [ Fecha de Pago]
            ELSE [ Fecha de Pago]
        END, 103) AS [Fecha de Pago funcion],



        /*------------------------------Entrada a Cruce -----------------------------*/
        [Fecha primera Selección],



        /*------------------------------ Etiqueta de fecha factura -----------------------------*/
        CuentaG_FechaFactura AS "FECHA DE FACTURACIÓN",

        /*  FECHA QUE RECIBE FACTURA  */
        CONVERT(VARCHAR(10), [FAC RECEPCION EXP. A FACTURACION], 103) AS "FECHA RECIBE FACT",

        CONVERT(VARCHAR(10),[Fechas de Cuentas de Gastos], 103) AS [FECHA TIMBRADO],



        /*------------------------------ etiqueta de entrega de mercancia y fecha factura -----------------------------*/
        CuentaG_FechaFactura,


        /*------------------------------ Campos de clasificación -----------------------------*/
        [Clave Pedimento],
        Ejecutivo_ABC,
        [Guia Master],
        [Guia House],
        [Tipo Operación Desc],
        COALESCE(MERC.MercanciaFinal, main.Mercancía) AS Mercancía,
        CASE 
            --WHEN main.Mercancía IN (
            --    'INSULINA GLARGINA MAL ESCRITA',
            --    'VACUNA INFLUENZA MAL ESCRITA',
            --    'HEPARINA SODICA MAL ESCRITA',
            --    'MEDICAMENTO X CON ERROR',
            --    'PRODUCTO Y MAL ESCRITO'
            --    -- Agrega aquí todos los medicamentos mal escritos
            --) THEN 'PRODUCTIVO'
            
            --/* CORRECCIONES PARA NOMBRES SIMILARES */
            --WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) IN (
            --    'OTRO MEDICAMENTO MAL ESCRITO',
            --    'ALGUN PRODUCTO CON FALLA ORTOGRAFICA'
            --) THEN 'NO PRODUCTIVO'
            
            /* CORRECCIONES ESPECÍFICAS CON PATRONES */
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AUBAGIO%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ADACELBOOST%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ALDURAZYME%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AMARYL%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ARAVA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BEYFORTUS%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BI PROFENID%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BI-PROFENID%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BENEFLUR%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BISULFATO%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BUSCAPINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CAJAS COLECTIVAS%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CAPRELSA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CEREZYME (IMIGLUCERASA)%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 40MG/0.4ML INJ PS2%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE (ENOXAPARINA SODICA)%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE  (ENOXAPARINA SODICA)%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 6KIU/0.6ML INJ PS2 PRV M24 MX%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 60MG/0.6ML INJ PS2%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 2 SOL INY%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLONAZEPAM%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLOPIDOGREL HIDROGENOSULFATO GRANULADO%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%COPLAVIX%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%COPLAVIX 75/100 TABCO 4X7 MX%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPIXENT%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ELOXATIN%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ELOXATIN 50MG/10ML%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ENTEROGERMINA %' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ENTEROGERMINA 2BCFU%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FABRAZYME%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FLAGYL%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FUROSEMIDA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HEXACIMA 5 ML 10%' THEN 'PRODUCTIVO' --REVISAR
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HEXACIMA VACUNA%' THEN 'PRODUCTIVO' --REVISAR
            
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%JEVTANA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS%' THEN 'PRODUCTIVO' --REVISAR
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS 1KIU/10ML INJ VL1 M24 MX%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS 100 UI/ML VIAL 1X10ML%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS INSULINA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LASIX%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LEMTRADA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MENACTRA %' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MOZOBIL%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MYOZYME%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%NIRSEVIMAB%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%NOVALGINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PARACETAMOL%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PROFENID%' THEN 'PRODUCTIVO' --REVISAR
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REGIVAS%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REZUROCK%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFADIN%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFOCINA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFOCYNA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIVAROXABAN%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SARCLISA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SHORANT%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 2BCFU%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 4BCFU/5ML SUSP BT%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 1%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 2%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE S%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SOLIQUA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STAMARIL (VACUNA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STAMARIL VACUNA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STILNOX%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SUPLEMENTO VISCOELEASTI%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SYNVISC%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TAXOTERE%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%THYROGEN%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TIMOGLOBULINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TOUJEO%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TOUJEO INSULINA  GLARGINA%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TUBERSOL DER%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TYPHIM V%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VAXIGRIP TETRA%' THEN 'PRODUCTIVO' --REVISAR
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VERORAB%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%XATRAL OD%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ZALTRAPZIV%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%METAMIZOL SODICO%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%GUAIFENESINA USP-NF-2025%' THEN 'PRODUCTIVO'
            WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 20MG/0.4ML INJ PS2 PRV M24 MX (MEDICAMENTOS DOSIFICADO DE USO HUMANO)%' THEN 'PRODUCTIVO'

            /* PATRONES PARA NO PRODUCTIVOS */
           
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%INFLUENZA ANTIGEN A/MICHIGAN/105/2025 (SAN-049A) (H3N2)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DTAP (DAPTACEL) QC CRIT REAGENT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RILIPRUBART 1200%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RILIPRUBART 300%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE RILZABRUTINIB 400 MG O PLACEBO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ANTI HI OUCHTERLONY%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AG A/MICH/105/2025 SAN049A%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%A/MICHIGAN/105/2025-SAN-049A%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SOL PRP 0.15 UG/ML HYDROLYSEE SST%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%059%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%094 TETRAVAC%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%095 ACT HIB%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%25 DESA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ACCESORIO PARA EQUIPOS DE APLICACION DE SOLUCIONES%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '% A/SWITZERLAND/6849/2025 (IVR-278) INFLUENZA VIRUS ANTIGEN%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ACCESORIO PARA APARATO DE USO MEDICO (FILTROS)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ACCESORIOS PARA APARATO DE USO MEDICO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ACCESORIOS PARA TUBERIA DE PLASTICO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ACCESORIOS PARA TUBERIA DE PLASTICO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ÁCIDO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AG A/VICTORIA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AG A/SWITZ%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%A/SWITZER%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AGUA PARA INYECCION%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AMISULPRIDE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ALLEGRA%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AMLITELIMAB%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AMORTIGUADOR%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%APARATO DE CONTROL%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%APRATO DE USO MEDICO CON ACCESORIO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%APARATO PARA CALIBRACION CON ACC%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%APARATO PARA CALIBRACION%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%APARATO PARA LA TRANSMISION%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%APROVASC%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AROS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AS A VICTORIA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AS A/CROATIA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BCGIT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BCG IT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BCG-IT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BRILLIANT BLUE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%B.M.I.-AMIODARONE HCI EUR%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CHUMACERAS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE  (ENOXAPARINA SODICA)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%COATING%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CORREA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CP MOUSE REFERENCE STANDARD%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DATAPCEL%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DETECTOR%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DESINFECTANTE%' THEN 'NO PRODUCTIVO' --REVISAR
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DICHLORO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DISCOS DE RUPTURA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPILUMAB 300MG%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPILUMAB 300 MG%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%EMPTY SHIPPERS (C%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%EQUIPO DE VISION%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%EQUIPO PARA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%EQUIPOS PARA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%EQUIPOS PARA LA TOMA Y CONSERVACION%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ERGANOL%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ESTUCHE DE PLASTICO%' THEN 'NO PRODUCTIVO' -- NO CLASIFDICADO
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ETIQUETA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ETIQUETAS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FORMALINA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FILTRO DE ACEITE CON ACCESORIOS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FRASCO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FUENTE DE PODER%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%GOAT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%GRABADOR DE%' THEN 'NO PRODUCTIVO' --NO CLASIFICADO
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%GUANTES%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HEIFER%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HERRAJE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HISOPOS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HOJAS PAPEL FILTRO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HOJAS DE  PAPEL FILTRO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HORSE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HYDRAGEL%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%IMPRESORA POR INYECCION DE TINTA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%IMPRESOS EN HOJAS SUELTAS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%INFLUENZA ANTI-A%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%INHIBIDOR DE PROTEASA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%INSTRUMENTO DE ENS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%Interruptore%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%INTERRUPTOR ELECTRICO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%IRBESARTAN%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ISATUXIMAB 500MG/25ML %' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ISATUXIMAB 500%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%JUNTAS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KIT DE DIS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KIT DE PRUEBA AGUA PARA INYECCION%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KIT DE TOM%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KIT ISOTE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KIT PARA LATO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KIT DE LABORATORIO PARA LA TOMA DE MUESTRAS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KITS PARA LA TOMA DE MUESTRAS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%KITS PARA LATO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LAPTOP%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LECTOR OPTICO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MANUAL EN IDIOMA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MANUFACTURAS DE PLASTICO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MANGAS %' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MANGERAS DE SILICON%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MEDIDOR DE FLUJO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MEDIOS DE CULTIVO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MEDIOSDE CULTIVO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MENACTRA VACUNA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MERCURY STANDAR%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%METRONIDAZOL%' THEN 'NO PRODUCTIVO' --NO CLASIFICADO
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MMR II%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MOCHILA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUCOANGIN%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MONITOR%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MONOVALENT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRA DE DUPILUMAB 300MG/2ML SOLUCION (150MG/ML) O PLACEBO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE AMLITELIMAB%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE AM%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE DEXAMETASONA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE DUPILUMAB%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE FREXALIMAB 1200 MG/8 ML%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE ITE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE L%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE RILIPRUBART%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS RILIPRUBART%' THEN 'NO PRODUCTIVO' --REVISAR
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE SAR443122%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE SAR4437%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE TE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE VA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE VACUNA PCV21%' THEN 'NO PRODUCTIVO' --NO CLASIFICADO
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE VACUNA RSVT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE VE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRA DE VYF%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DU%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS IT%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE SAR442168%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS SAR443122%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE ST%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DUPILUMAB 300MG/2ML (150MG/ML)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS TERIFLUNOMIDE 14 MG O PLACEBO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%N. MENINGITIDIS%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%NEXVIADYME%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%OXIMETRO CON ACCESORIOS (SENSOR)%' THEN 'NO PRODUCTIVO' --NO TIENE CLASIFICACION
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PARTES%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PARTES PARA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PARTES PARA VACUOMETROS (TRANSDUCTOR)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PLERIXAFOR%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PRESOSTATOS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PREVNAR%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PRUEBAS DE EMBARAZO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PRUEBA DE EMBARAZO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PURIFIED FHA ANTIGEN%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REFERENCE HI OUCHTERLONY%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REF PRPC.%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RECIPIENTE DE PLASTICO CON TAPA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RESISTENCIAS CALENTADORAS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RODAMIENTO DE RODILL%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SISTEMA DE DEPURACION DE AIRE POR ACCION QUIMICA  (VHP SYSTEMS) CON ACCESORIOS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SISTEMA DE PROCESAMIENTO DE  DATOS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SISTEMA PARA EL PROCESA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SISTEMA DE PROCESAMIENTO DE DATOS (ADFIRMIA CODING MACHINE) CON ACCESORIOS PARA SU INSTALACION.%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SL79.0722-10N ALFUZOSIN%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SL85.0067-00%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SL89.0160-00%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SR24726A CLOPIDOGREL%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SODIUM ACETATE AMHYDROUS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SODIUM HY%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SULFATO DE HIDROXI%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SUPLEMENTO ALIMENTICIO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TAPONES%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TC20/FA GAMMA RAY TREATED CAPS (SELLOS)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TC20/FA PINK 20 (SELLOS)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TERMOMETRO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%THYMOGLOBULINE FI%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TORNILLO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TRANSDUCTOR DE PRESION CON ACCESORIO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TRITON X100%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TUBO%' then 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TYPHOID ANTISERUM%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%UNIDAD DE PROCESAMIENTO DE DATOS (LAPTOP)%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VACUNA VAX%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VALVULA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VALVULAE%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VIGORIMETRO%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VYF%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%XENPOZYME%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%YF-VAX%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ZOLPIDEM TARTA%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FILTRO DE ACEITE CON ACCESORIOS%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE M-M-R-II%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE ROTARIX 1.5ML%' THEN 'NO PRODUCTIVO'
           WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HIDROCORTISONA%' THEN 'NO PRODUCTIVO'
            
            /* CLASIFICACIÓN AUTOMÁTICA POR TABLAS */
            WHEN cm.Clasificacion = 'PRODUCTIVO' THEN 'PRODUCTIVO'
            WHEN cm.Clasificacion = 'NO PRODUCTIVO' THEN 'NO PRODUCTIVO'
            
            /* SI NO CUMPLE NINGUNA CONDICIÓN ANTERIOR */
            ELSE 'SIN CLASIFICACION'
        END AS "CLASIFICACIÓN DE MERCANCIA",


        /*------------------------------ FAMILIA DE MERCANCÍA (SOLO PARA PRODUCTIVO Y SIN CLASIFICACION) -----------------------------*/
        CASE 
            /* Solo asignar familia si la clasificación es PRODUCTIVO o SIN CLASIFICACION */
            WHEN 
                (CASE 
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AUBAGIO%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ADACELBOOST%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ALDURAZYME%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AMARYL%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ARAVA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BEYFORTUS%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BI PROFENID%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BI-PROFENID%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BENEFLUR%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BISULFATO%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BUSCAPINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CAJAS COLECTIVAS%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CAPRELSA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CEREZYME (IMIGLUCERASA)%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 40MG/0.4ML INJ PS2%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE (ENOXAPARINA SODICA)%' THEN 'PRODUCTIVO'
                wHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE  (ENOXAPARINA SODICA)%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 6KIU/0.6ML INJ PS2 PRV M24 MX%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 60MG/0.6ML INJ PS2%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 2 SOL INY%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLONAZEPAM%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLOPIDOGREL HIDROGENOSULFATO GRANULADO%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%COPLAVIX%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%COPLAVIX 75/100 TABCO 4X7 MX%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPIXENT%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ELOXATIN%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ELOXATIN 50MG/10ML%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ENTEROGERMINA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ENTEROGERMINA 2BCFU%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FABRAZYME%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FLAGYL%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FUROSEMIDA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HEXACIMA 5 ML 10%' THEN 'PRODUCTIVO' --REVISAR
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HEXACIMA VACUNA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%JEVTANA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS%' THEN 'PRODUCTIVO' --REVISAR
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS 1KIU/10ML INJ VL1 M24 MX%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS 100 UI/ML VIAL 1X10ML%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS INSULINA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LASIX%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LEMTRADA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MENACTRA %' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MOZOBIL%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MYOZYME%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%NIRSEVIMAB%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%NOVALGINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PARACETAMOL%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PROFENID%' THEN 'PRODUCTIVO' --REVISAR
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REGIVAS%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REZUROCK%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFADIN%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFOCINA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFOCYNA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIVAROXABAN%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SARCLISA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SHORANT%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 2BCFU%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 4BCFU/5ML SUSP BT%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 1%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 2%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE S%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SOLIQUA%' THEN 'PRODUCTIVO' --REVISAR SOLO3
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STAMARIL (VACUNA%' THEN 'PRODUCTIVO' --REVISAR
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STAMARIL VACUNA ANTIAMARILICA ATENUADA USO HUMANO%' THEN 'PRODUCTIVO' --REVISAR
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STILNOX%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SUPLEMENTO VISCOELEASTI%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SYNVISC%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TAXOTERE%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%THYROGEN%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TIMOGLOBULINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TOUJEO%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TOUJEO INSULINA  GLARGINA%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TUBERSOL DER%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TYPHIM V%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VAXIGRIP TETRA%' THEN 'PRODUCTIVO' --REVISAR
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VERORAB%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%XATRAL OD%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ZALTRAPZIV%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SR24726A CLOPIDOGREL%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%METAMIZOL SODICO%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%GUAIFENESINA USP-NF-2025%' THEN 'PRODUCTIVO'
                WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 20MG/0.4ML INJ PS2 PRV M24 MX (MEDICAMENTOS DOSIFICADO DE USO HUMANO)%' THEN 'PRODUCTIVO'

                    ELSE 'SIN CLASIFICACION'
                END) IN ('PRODUCTIVO', 'SIN CLASIFICACION')
            THEN
                CASE 
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) = 'SINUBERASE 4BCFU/5ML SUSP BT10 M24 MX' THEN 'CHC'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ADACELBOOST%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ALDURAZYME%' THEN 'HUÉRFANOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ALLEGRA%' THEN 'GENMED' --NO TIENE CLASIFICACION
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AMARYL%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ARAVA%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%AUBAGIO%' THEN 'Specialty Care'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BIPROFENID 150MG TABCR BL2X10 M2%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BI PROFENID%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BI-PROFENID%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BENEFLUR%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BISULFATO%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%BUSCAPINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CAJAS COLECTIVAS%' THEN 'CHC'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CAPRELSA%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CEREZYME (IMIGLUCERASA)%' THEN 'HUÉRFANOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 40MG/0.4ML INJ PS2%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE (ENOXAPARINA SODICA)%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE  (ENOXAPARINA SODICA)%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 6KIU/0.6ML INJ PS2 PRV M24 MX%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 60MG/0.6ML INJ PS2%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 2 SOL INY%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLONAZEPAM%' THEN 'MATERIA PRIMA'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLOPIDOGREL HIDROGENOSULFATO GRANULADO%' THEN 'MATERIA PRIMA'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%COPLAVIX%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%COPLAVIX 75/100 TABCO 4X7 MX%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPIXENT 200MG/1,14ML%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPIXENT 200MG/+ INJ PS2 SAFE M36 MX%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPIXENT 2 SOL INY 300mg/2mL%' THEN 'Specialty Care'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ELOXATIN%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ELOXATIN 50MG/10ML%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ENTEROGERMINA %' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ENTEROGERMINA 2BCFU%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FABRAZYME%' THEN 'HUÉRFANOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FABRAZYME 5MG/1ML INJPO VL1 2NDG M36 MX%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FUROSEMIDA%' THEN 'MATERIA PRIMA'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%FLAGYL%' THEN 'GENMED' --NO TIENE CLASIFICACION
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HEXACIMA 5 ML 10%' THEN 'BIOLÓGICOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%HEXACIMA VACUNA%' THEN 'VAX' 
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%JEVTANA%' THEN 'Specialty Care'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS%' THEN 'GENMED' 
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS 1KIU/10ML INJ VL1 M24 MX%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS 100 UI/ML VIAL 1X10ML%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LANTUS INSULINA%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LASIX%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%LEMTRADA%' THEN 'Specialty Care'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MUESTRAS DE SAR442168%' THEN 'PRODUCTIVO' -- NO CLASIFICADO
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MOZOBIL%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MENACTRA %' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%METRONIDAZOL%' THEN 'NO PRODUCTIVO' --NO CLASIFICADO
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%MYOZYME%' THEN 'HUÉRFANOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%NIRSEVIMAB%' THEN 'RSV'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%NOVALGINA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                    --WHEN main.Mercanc�a LIKE '%OSCILOMETRIA%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PARACETAMOL%' THEN 'MATERIA PRIMA'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%PROFENID%' THEN 'PRODUCTIVO' --REVISAR
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REGIVAS%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%REZUROCK%' THEN 'HUÉRFANOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFADIN%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFOCINA%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIFOCYNA%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%RIVAROXABAN%' THEN 'MATERIA PRIMA'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SARCLISA%' THEN 'HUÉRFANOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SHORANT%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE%' THEN 'CHC'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 2BCFU%' THEN 'CHC'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE 4BCFU/5ML SUSP BT%' THEN 'CHC'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SINUBERASE%' THEN 'CHC'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SOLIQUA%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STAMARIL (VACUNA%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STAMARIL VACUNA ANTIAMARILICA ATENUADA USO HUMANO%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STILNOX 28%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STILNOX CR 12.5mg %' THEN 'PSICOTRÓPICOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STILNOX CR%' THEN 'PSICOTRÓPICOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%STILNOX TA%' THEN 'PSICOTRÓPICOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SUPLEMENTO VISCOELEASTI%' THEN 'PRODUCTIVO' --NO TIENE CLASIFICACION
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SYNVISC%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TAXOTERE%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%THYROGEN%' THEN 'HUÉRFANOS'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TIMOGLOBULINA%' THEN 'GENMED' 
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TOUJEO%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TOUJEO INSULINA  GLARGINA%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TUBERSOL DER%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%TYPHIM V%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VAXIGRIP TETRA%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%VERORAB%' THEN 'VAX'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%XATRAL OD%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%ZALTRAPZIV%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%DUPIXENT%' THEN 'GENMED'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%SR24726A CLOPIDOGREL%' THEN 'MATERIA PRIMA'
                    WHEN COALESCE(MERC.MercanciaFinal, main.Mercancía) LIKE '%CLEXANE 20MG/0.4ML INJ PS2 PRV M24 MX (MEDICAMENTOS DOSIFICADO DE USO HUMANO)%' THEN 'GENMED'
                    ELSE 'SIN FAMILIA' 
                END
            ELSE NULL -- Para 'NO PRODUCTIVO' será NULL
        END AS FAMILIA,
    
        [Tipo Mercancía] AS "TIPO DE MERCANCIA",
        Cliente,
        [EJE UNIDAD DE NEGOCIO] AS "Unidad de negocio",
        [MOTIVO DE RETRASO],
        [MOTIVO DE RETRASO OTRO],
        CASE
            WHEN [MOTIVO DE RETRASO] = 'OTRO' THEN [MOTIVO DE RETRASO OTRO]
            ELSE [MOTIVO DE RETRASO]
        END AS "MOTIVO DE RETRASO COMPLETO", 
        Ejecutivo_Tipo_Mercancia,
        [Primera Selección],
        [TRANSPORTISTA.],
        RFC_Importador,
        OtrosIncPed,
        Nico,
        Mercancia_CovesSubModelo,
        [Días Credito],
        [Valor Moneda Factura ],
        [UMT DESCRIPCION],
        [Recti A Cargo De],
        [Motivo de Rectificación],
        [Nombre País Origen/Destino],
        [Nombre País Vendedor/Comprador],
        [Clave de País Origen/Destino],
        [Clave de País Vendedor/Comprador],
        [UNIDAD RENTADA],
        [PLACAS RENTADA],
        [UNIDAD SUPER EXPRESS],
        [PLACAS SUPER EXPRESS],
        [EMBARQUE REFRIGERADO],
        [MedioArribo],
        [Medio],
        [MedioTransporte],
        [Rectificación Realizada Por]

    FROM [SIR].[Admin].[SIR_VT_Sabana_Pedimento_ABC] main
    LEFT JOIN RefEntradaPorPedimento AS REF_E
        ON REPLACE(TRIM(main.Referencia), '/', '') = REF_E.ReferenciaNormalizada
        AND RIGHT(TRIM(CAST(main.Pedimento AS VARCHAR(20))), 7) = REF_E.PedimentoUltimos7
    LEFT JOIN RefEntradaPorReferencia AS REF_E2
        ON REPLACE(TRIM(main.Referencia), '/', '') = REF_E2.ReferenciaNormalizada
    OUTER APPLY (
        SELECT
            CASE
                WHEN main.Sucursal = 'CORRESPONSALIAS'
                     OR main.Referencia LIKE '%LT%'
                     OR main.Referencia LIKE '%MNS%'
                    THEN COALESCE(
                        REF_E.MercanciaRefPedimento,
                        NULLIF(TRIM(main.Mercancía), ''),
                        REF_E2.MercanciaRefReferencia
                    )
                ELSE COALESCE(
                    NULLIF(TRIM(main.Mercancía), ''),
                    REF_E.MercanciaRefPedimento,
                    REF_E2.MercanciaRefReferencia
                )
            END AS MercanciaFinal
    ) AS MERC
    /* JOIN para clasificación de mercancías CON COLLATION CORREGIDO */
    LEFT JOIN ClasificacionMercancias cm ON COALESCE(MERC.MercanciaFinal, main.Mercancía) COLLATE SQL_Latin1_General_CP1_CI_AS = cm.[DESCRIPCIÓN_PRODUCTO]

    WHERE 
        (Cliente IN ('SANOFI PASTEUR, S.A DE C.V.','AZTECA VACUNAS, SA DE CV')
        --(Cliente IN ('AZTECA VACUNAS, SA DE CV')
        OR (Cliente LIKE '%AVENTIS%' AND [EJE UNIDAD DE NEGOCIO] LIKE'GENMED%'))
        --AND [Tipo Operación Desc] = 'Importación'
        --and [Clave Pedimento] not like 'R%'
        --AND [Mercancía] like '%CLEXANE%'
)

SELECT *
FROM ConsultaBase
WHERE --"CLASIFICACIÓN DE MERCANCIA" IN ('PRODUCTIVO','SIN CLASIFICACION') --('PRODUCTIVO','SIN CLASIFICACION')
   --AND 
   (
    -- Convertir el campo unificado de vuelta a DATE para la comparación
             TRY_CONVERT(DATE, [Fecha de Pago funcion], 103) >= '2023-01-01'
             AND TRY_CONVERT(DATE, [Fecha de Pago funcion], 103) <= '2024-12-31')
--[MOTIVO DE RETRASO COMPLETO] not like 'NULL'
AND [Sucursal] like '%CORRESPONSALIAS%'
--and Referencia = 'MNSI238348'
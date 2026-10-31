import streamlit as st
import pandas as pd
from src.auth import (
    check_permission,
    create_user,
    list_users,
    reset_user_password,
    set_user_active,
    set_user_role,
)
from src.crud import (
    create_product,
    delete_product,
    normalize_product_storage_types,
    update_product,
)
import datetime
import math
import os
from src.reporting import dataframe_to_csv, excel_workbook_bytes
from src.backup import (
    BackupError,
    backup_fingerprint,
    create_database_backup,
    get_backup_restore_audit,
    restore_backup_to_test_database,
    validate_backup_archive,
)

def _product_ids(frame):
    if "product_id" not in frame:
        return []

    def sort_key(value):
        text = str(value).strip()
        return (0, int(text)) if text.isdigit() else (1, text.casefold())

    return sorted(frame["product_id"].dropna().unique().tolist(), key=sort_key)


def _form_integer(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0
    return int(number) if math.isfinite(number) and number.is_integer() and number >= 0 else 0


def show(df_products):
    st.subheader("Quản trị hệ thống và dữ liệu")
    
    # Kiểm tra phân quyền Admin
    if not check_permission("admin"):
        st.error("Truy cập bị từ chối. Bạn không có quyền quản trị viên để thao tác trang này.")
        return
        
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Thêm / Sửa / Xóa Sản phẩm",
            "Sao lưu Cơ sở dữ liệu (Backup)",
            "Phục hồi Dữ liệu (Restore)",
            "Nhật ký Backup / Restore",
            "Báo cáo",
            "Quản lý người dùng",
        ]
    )
    
    with tab1:
        action = st.radio(
            "Chọn thao tác dữ liệu",
            [
                "Danh sách / Chi tiết",
                "Thêm sản phẩm",
                "Cập nhật sản phẩm",
                "Xóa vĩnh viễn",
                "Chuẩn hóa kiểu dữ liệu",
            ],
        )
        # app.py already provides the active, cached product dataset for this page.
        current_products = df_products.copy()

        if action == "Danh sách / Chi tiết":
            st.markdown("### Danh sách sản phẩm đang hoạt động")
            if current_products.empty:
                st.info("Chưa có sản phẩm để hiển thị.")
            else:
                st.dataframe(current_products, use_container_width=True, hide_index=True)
                product_ids = _product_ids(current_products)
                selected_id = st.selectbox("Xem chi tiết theo mã sản phẩm", product_ids)
                product = current_products[current_products["product_id"].astype(str) == str(selected_id)]
                if product.empty:
                    st.error("Không tìm thấy sản phẩm.")
                else:
                    st.json(product.iloc[0].to_dict())

        elif action == "Thêm sản phẩm":
            st.caption(
                "Mã sản phẩm phải duy nhất; giá và số lượng là số nguyên không âm. "
                "Doanh thu ước tính được tính từ giá × số lượng."
            )
            with st.form("add_form"):
                p_id = st.text_input("Mã sản phẩm", help="Chỉ gồm chữ số; được lưu dưới dạng chuỗi.")
                p_name = st.text_input("Tên sản phẩm")
                p_price = st.number_input("Đơn giá (VNĐ)", min_value=0, step=1000)
                p_qty = st.number_input("Số lượng đã bán", min_value=0, step=1)
                submitted = st.form_submit_button("Thêm bản ghi")
                if submitted:
                    success, msg = create_product(
                        {
                            "product_id": p_id,
                            "name": p_name,
                            "price": p_price,
                            "quantity_sold": p_qty,
                        }
                    )
                    (st.success if success else st.error)(msg)
                    if success:
                        st.rerun()

        elif action == "Cập nhật sản phẩm":
            if current_products.empty:
                st.info("Không có sản phẩm đang hoạt động để cập nhật.")
            else:
                product_ids = _product_ids(current_products)
                p_id = st.selectbox("Chọn mã sản phẩm", product_ids, key="update_product_id")
                selected_product = current_products[
                    current_products["product_id"].astype(str) == str(p_id)
                ].iloc[0]
                with st.form("update_form"):
                    new_name = st.text_input("Tên sản phẩm", value=str(selected_product.get("name", "")))
                    new_price = st.number_input(
                        "Đơn giá (VNĐ)",
                        min_value=0,
                        value=_form_integer(selected_product.get("price", 0)),
                        step=1000,
                    )
                    new_quantity = st.number_input(
                        "Số lượng đã bán",
                        min_value=0,
                        value=_form_integer(selected_product.get("quantity_sold", 0)),
                        step=1,
                    )
                    update_submitted = st.form_submit_button("Lưu thay đổi")
                if update_submitted:
                    success, msg = update_product(
                        p_id,
                        {
                            "name": new_name,
                            "price": new_price,
                            "quantity_sold": new_quantity,
                        },
                    )
                    (st.success if success else st.error)(msg)
                    if success:
                        st.rerun()

        elif action == "Xóa vĩnh viễn":
            st.caption(
                "Thao tác xóa sẽ loại bản ghi sản phẩm khỏi cơ sở dữ liệu và không thể khôi phục từ ứng dụng."
            )
            active_ids = _product_ids(df_products)
            if active_ids:
                delete_id = st.selectbox("Chọn sản phẩm cần xóa vĩnh viễn", active_ids)
                confirm_delete = st.checkbox(
                    f"Tôi hiểu sản phẩm {delete_id} sẽ bị xóa vĩnh viễn",
                    key="confirm_permanent_delete",
                )
                if st.button("Xóa vĩnh viễn khỏi CSDL", type="primary", disabled=not confirm_delete):
                    success, msg = delete_product(delete_id)
                    (st.success if success else st.error)(msg)
                    if success:
                        st.rerun()
            else:
                st.info("Không có sản phẩm để xóa.")

        else:
            st.caption(
                "Chuẩn hóa Product ID về chuỗi; giá, số lượng và doanh thu về Int64. "
                "Các bản ghi không hợp lệ hoặc trùng mã sẽ được giữ nguyên để tránh mất dữ liệu."
            )
            confirmed = st.checkbox(
                "Tôi đã sao lưu và đồng ý chuẩn hóa các bản ghi hợp lệ",
                key="confirm_normalize_product_ids",
            )
            if st.button("Chuẩn hóa kiểu dữ liệu sản phẩm", type="primary", disabled=not confirmed):
                success, msg = normalize_product_storage_types()
                (st.success if success else st.error)(msg)
                if success:
                    st.rerun()
                
    with tab2:
        st.markdown("### Sao lưu dữ liệu")
        st.caption("Bản sao lưu ZIP gồm tất cả collection clean_* trong allowlist, giữ nguyên kiểu dữ liệu MongoDB.")
        if st.button("Tạo bản sao lưu cơ sở dữ liệu"):
            try:
                backup_data, created_at, collection_counts = create_database_backup()
            except Exception as error:
                st.error(f"Sao lưu thất bại: {error}")
            else:
                st.session_state["database_backup"] = backup_data
                st.session_state["database_backup_created_at"] = created_at
                st.session_state["database_backup_counts"] = collection_counts
                st.success(f"Sao lưu thành công lúc {created_at} (UTC).")
        if "database_backup" in st.session_state:
            st.json(st.session_state["database_backup_counts"])
            backup_timestamp = datetime.datetime.fromisoformat(
                st.session_state["database_backup_created_at"]
            ).strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "Tải bản sao lưu cơ sở dữ liệu (.zip)",
                st.session_state["database_backup"],
                f"tiki_clean_database_{backup_timestamp}.zip",
                "application/zip",
            )
            
    with tab3:
        st.markdown("### Phục hồi dữ liệu")
        st.warning(
            "Phục hồi chỉ ghi vào cơ sở dữ liệu thử nghiệm riêng có hậu tố "
            "`_restore_test`; không ghi vào cơ sở dữ liệu dữ liệu nhóm."
        )
        uploaded_file = st.file_uploader(
            "Tải lên bản sao lưu cơ sở dữ liệu (.zip)",
            type=["zip"],
            key="database_restore_upload",
        )
        if uploaded_file and st.button("Kiểm tra bản sao lưu", key="validate_database_backup"):
            try:
                validated_backup = validate_backup_archive(uploaded_file.getvalue())
            except (BackupError, OSError, ValueError, UnicodeDecodeError) as error:
                st.session_state.pop("validated_database_backup", None)
                st.error(f"Bản sao lưu không hợp lệ: {error}")
            else:
                st.session_state["validated_database_backup"] = validated_backup
                st.session_state["validated_database_backup_fingerprint"] = backup_fingerprint(
                    uploaded_file.getvalue()
                )
                st.success(
                    f"Bản sao lưu hợp lệ, tạo lúc {validated_backup.created_at} (UTC). "
                    "Chưa có dữ liệu nào được phục hồi."
                )
                st.json(validated_backup.counts)

        validated_backup = st.session_state.get("validated_database_backup")
        target_db_name = os.environ.get(
            "TIKI_RESTORE_TEST_DB_NAME",
            "tikilens_vn_restore_test",
        ).strip()
        current_upload_matches = (
            uploaded_file is not None
            and st.session_state.get("validated_database_backup_fingerprint")
            == backup_fingerprint(uploaded_file.getvalue())
        )
        if validated_backup is not None and current_upload_matches:
            st.error(
                f"Thao tác sẽ thay thế dữ liệu trong `{target_db_name}`. "
                "Không ảnh hưởng database nhóm `tikilens_vn`."
            )
            confirmation = st.text_input(
                f"Nhập chính xác `{target_db_name}` để xác nhận",
                key="restore_test_database_confirmation",
            )
            if st.button(
                "Phục hồi vào database thử nghiệm",
                type="primary",
                disabled=confirmation != target_db_name,
            ):
                try:
                    restored_database, restored_counts = restore_backup_to_test_database(
                        validated_backup
                    )
                except Exception as error:
                    st.error(f"Phục hồi thất bại: {error}")
                else:
                    st.success(
                        f"Phục hồi thành công vào `{restored_database}` lúc "
                        f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} (UTC)."
                    )
                    st.json(restored_counts)
        elif validated_backup is not None:
            st.info("Hãy kiểm tra lại đúng file sao lưu đang tải lên trước khi phục hồi.")

    with tab4:
        st.markdown("### Nhật ký sao lưu và phục hồi")
        try:
            audit_rows = get_backup_restore_audit()
        except Exception as error:
            st.error(f"Không đọc được nhật ký thao tác: {error}")
        else:
            if audit_rows:
                st.dataframe(pd.DataFrame(audit_rows), width="stretch", hide_index=True)
            else:
                st.info("Chưa có thao tác sao lưu hoặc phục hồi nào được ghi nhận.")

    with tab5:
        st.markdown("### Báo cáo dữ liệu sản phẩm")
        if df_products.empty:
            st.info("Không có dữ liệu để lập báo cáo.")
            return

        report = df_products.copy()
        revenue_column = "estimated_revenue" if "estimated_revenue" in report else "revenue_estimate"
        if revenue_column not in report:
            price = pd.to_numeric(report.get("price", pd.Series(0, index=report.index)), errors="coerce").fillna(0)
            quantity = pd.to_numeric(
                report.get("quantity_sold", pd.Series(0, index=report.index)), errors="coerce"
            ).fillna(0)
            report["report_revenue"] = price * quantity
            revenue_column = "report_revenue"
        report[revenue_column] = pd.to_numeric(report[revenue_column], errors="coerce").fillna(0)

        metrics = st.columns(3)
        metrics[0].metric("Số sản phẩm", f"{len(report):,}")
        metrics[1].metric("Tổng doanh thu ước tính", f"{report[revenue_column].sum():,.0f} ₫")
        metrics[2].metric(
            "Số nhà bán",
            f"{report['seller_id'].nunique():,}" if "seller_id" in report else "—",
        )

        category_column = (
            "root_category_name"
            if "root_category_name" in report
            else "category_name"
        )
        if category_column not in report:
            report[category_column] = "Chưa phân loại"
        category_report = (
            report.groupby(category_column, dropna=False)
            .agg(
                product_count=(revenue_column, "size"),
                estimated_revenue=(revenue_column, "sum"),
            )
            .reset_index()
            .rename(columns={category_column: "category_name"})
            .sort_values("estimated_revenue", ascending=False)
        )
        st.dataframe(category_report, width="stretch", hide_index=True)

        kpi_report = pd.DataFrame(
            [
                ("Số sản phẩm", len(report)),
                ("Tổng doanh thu ước tính (VNĐ)", report[revenue_column].sum()),
                (
                    "Số nhà bán",
                    report["seller_id"].nunique() if "seller_id" in report else 0,
                ),
            ],
            columns=["Chỉ số", "Giá trị"],
        )
        st.download_button(
            "Tải toàn bộ dữ liệu sản phẩm (CSV)",
            lambda: dataframe_to_csv(report),
            "tiki_products_report.csv",
            "text/csv",
        )
        st.download_button(
            "Tải báo cáo tổng hợp (Excel)",
            lambda: excel_workbook_bytes(
                {
                    "KPI": kpi_report,
                    "Danh muc": category_report,
                    "San pham": report,
                }
            ),
            "tiki_admin_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with tab6:
        st.markdown("### Quản lý tài khoản")
        users = list_users()
        if users:
            user_table = pd.DataFrame(users).rename(
                columns={
                    "username": "Tên đăng nhập",
                    "display_name": "Tên hiển thị",
                    "role": "Vai trò",
                    "is_active": "Đang hoạt động",
                    "created_at": "Ngày tạo",
                }
            )
            user_table["Đang hoạt động"] = user_table["Đang hoạt động"].map(
                {1: "Có", 0: "Không", True: "Có", False: "Không"}
            )
            st.dataframe(user_table, use_container_width=True, hide_index=True)

        create_tab, update_tab = st.tabs(["Tạo tài khoản", "Cập nhật tài khoản"])
        with create_tab:
            with st.form("create_user_form"):
                username = st.text_input("Tên đăng nhập mới")
                display_name = st.text_input("Tên hiển thị")
                role = st.selectbox("Vai trò", ["user", "admin"], format_func=lambda value: "Người dùng" if value == "user" else "Quản trị viên")
                password = st.text_input("Mã PIN tạm thời (tối đa 6 số)", type="password", max_chars=6, help="Chỉ dùng chữ số 0–9, tối đa 6 số.")
                confirm_password = st.text_input("Nhập lại mã PIN", type="password", max_chars=6)
                submitted = st.form_submit_button("Tạo tài khoản")
            if submitted:
                if password != confirm_password:
                    st.error("Hai mã PIN không khớp.")
                else:
                    success, message = create_user(username, display_name, password, role)
                    (st.success if success else st.error)(message)
                    if success:
                        st.rerun()

        with update_tab:
            if not users:
                st.info("Chưa có tài khoản để cập nhật.")
            else:
                selected_username = st.selectbox(
                    "Chọn tài khoản",
                    [user["username"] for user in users],
                    key="managed_user",
                )
                selected_user = next(user for user in users if user["username"] == selected_username)
                role_options = ["user", "admin"]
                selected_role = st.selectbox(
                    "Vai trò mới",
                    role_options,
                    index=role_options.index(selected_user["role"]),
                    format_func=lambda value: "Người dùng" if value == "user" else "Quản trị viên",
                )
                if st.button("Cập nhật vai trò"):
                    success, message = set_user_role(selected_username, selected_role)
                    (st.success if success else st.error)(message)
                    if success:
                        st.rerun()

                active_value = bool(selected_user["is_active"])
                if selected_username == st.session_state.get("username"):
                    st.caption("Không thể vô hiệu hóa tài khoản đang đăng nhập.")
                elif st.button("Vô hiệu hóa tài khoản" if active_value else "Kích hoạt tài khoản"):
                    success, message = set_user_active(selected_username, not active_value)
                    (st.success if success else st.error)(message)
                    if success:
                        st.rerun()

                with st.form("reset_user_password_form"):
                    new_password = st.text_input("Mã PIN mới (tối đa 6 số)", type="password", max_chars=6, help="Chỉ dùng chữ số 0–9, tối đa 6 số.")
                    confirm_new_password = st.text_input("Nhập lại mã PIN mới", type="password", max_chars=6)
                    reset_submitted = st.form_submit_button("Đặt lại mã PIN")
                if reset_submitted:
                    if new_password != confirm_new_password:
                        st.error("Hai mã PIN không khớp.")
                    else:
                        success, message = reset_user_password(selected_username, new_password)
                        (st.success if success else st.error)(message)

import React from "react";
import { Separator } from "../../../../components/ui/separator";

export const FooterSection = (): JSX.Element => {
    const companyInfo = {
        name: "좌절금지(주)",
        ceo: "안희원",
        address: "서울 강남구 강남대로 364 미왕빌딩 10-11층, 17층 1707호",
        tel: "02-518-4831",
        year: "2025",
        companyNameEn: "No_frustration",
    };

    return (
        <footer
        className="
            py-8 mt-8
            w-full max-w-[992px] mx-auto
            font-['Roboto',Helvetica]
        "
        >
        <Separator className="w-full mb-6" />
        <div className="w-full text-[11px] leading-4 text-[#d9d9d9]">
            <p className="font-semibold tracking-[0.06px]">
            상호명 및 호스팅 서비스 제공 : {companyInfo.name}
            <br />
            대표이사 : {companyInfo.ceo}, 주소: {companyInfo.address}, Tel: {companyInfo.tel}
            <br />
            {companyInfo.name}는 통신판매중개자로서 오픈마켓 3I1E의 거래당사자가 아니며, 입점판매자가 등록한 상품정보 및 거래에 대해 {companyInfo.name}는 일체 책임을 지지 않습니다.
            <br />
            고객센터 / 전자금융거래분쟁담당
            <br />
            Copyright © {companyInfo.year} {companyInfo.companyNameEn} Co.,Ltd. All Rights Reserved.
            </p>
        </div>
        </footer>
    );
};

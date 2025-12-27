import React from "react";
import { Button } from "../../../../components/ui/button";
import logo from "../../../../assets/logo.png";
import cartIcon from "../../../../assets/icon-cart.png";

export const NavigationBarSection = (): JSX.Element => {
    const navItems = [
        { id: 1, text: "Category" },
        { id: 2, text: "Community" },
        { id: 3, text: "Favorate" },
        { id: 4, text: "Profile" },
    ];

    return (
        <div className="w-full max-w-[990px] mx-auto mt-[15px]">
            {/* ────────── 1줄: 로고 · 검색창 · 장바구니 ────────── */}
            <div className="relative flex items-center justify-between h-[65px]">
                {/* 로고 */}
                <div className="w-[188px] h-[65px] overflow-hidden flex items-center justify-center">
                    <img
                        src={logo}
                        alt="Logo"
                        className="w-[120px] h-[120px] object-cover object-left"
                    />
                </div>

                {/* 검색창 (전체 너비 기준 가운데 정렬) */}
                <form className="absolute left-1/2 transform -translate-x-1/2 w-[540px]">
                    <div className="flex">
                        <button
                            id="dropdown-button"
                            type="button"
                            className="shrink-0 z-10 inline-flex items-center py-2.5 px-4 text-sm font-medium text-gray-900 bg-gray-100 border border-gray-300 rounded-s-lg hover:bg-gray-200 focus:ring-4 focus:outline-none focus:ring-gray-100"
                        >
                            All categories
                            <svg
                                className="w-2.5 h-2.5 ml-2.5"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 10 6"
                                aria-hidden="true"
                            >
                                <path
                                    stroke="currentColor"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="m1 1 4 4 4-4"
                                />
                            </svg>
                        </button>

                        <div className="relative w-full">
                            <input
                                type="search"
                                id="search-dropdown"
                                required
                                placeholder="Search Mockups, Logos, Design Templates..."
                                className="block p-2.5 w-full z-20 text-sm text-gray-900 bg-gray-50 rounded-e-lg border-s-gray-50 border-s-2 border border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                            />
                            <button
                                type="submit"
                                className="absolute top-0 right-0 p-2.5 h-full text-sm font-medium text-white bg-blue-700 rounded-e-lg border border-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300"
                            >
                                <svg
                                    className="w-4 h-4"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 20 20"
                                    aria-hidden="true"
                                >
                                    <path
                                        stroke="currentColor"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"
                                    />
                                </svg>
                                <span className="sr-only">Search</span>
                            </button>
                        </div>
                    </div>
                </form>

                {/* 장바구니 (40 x 40 px, 각진 파란 배경 on hover) */}
                <Button
                    variant="ghost"
                    className="p-0 w-[40px] h-[40px] bg-transparent hover:bg-[#30b2e5] rounded-none flex items-center justify-center transition-colors"
                    aria-label="Shopping Cart"
                >
                    <img
                        src={cartIcon}
                        alt="Cart"
                        className="w-[40px] h-[40px] object-contain"
                    />
                </Button>
            </div>

            {/* ────────── 2줄: 메뉴 ────────── */}
            <div className="flex h-14 mt-[15px] gap-[15px]">
                {navItems.map((item) => (
                    <Button
                        key={item.id}
                        variant="ghost"
                        className="flex-1 h-14 bg-[#30b2e5] text-white border border-[#30b2e5]
                       rounded-[12px] hover:bg-white hover:text-[#30b2e5] transition-colors"
                    >
                        {item.text}
                    </Button>
                ))}
            </div>
        </div>
    );
};
